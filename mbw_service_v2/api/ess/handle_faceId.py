
import json
import os
import io
import frappe
import json
from frappe import _
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from mbw_service_v2.api.common import (
    gen_response,
    get_employee_id,
    exception_handel,
    get_language
)

import requests
import base64
from datetime import datetime
from frappe.core.doctype.file.utils import delete_file
from frappe.utils.file_manager import (
    save_file
)
from mbw_service_v2.api.file import (
    verify,
    my_minio
)
from mbw_service_v2.config_translate import i18n

"""Begin FaceID"""


@frappe.whitelist(methods="GET")
def get_faceid_employee(**kwargs):
    try:
        employee_id = get_employee_id()
        faceids = frappe.db.get_list('ESS Employee FaceID', filters={
                                     "employee": employee_id}, fields=["name", "url"], order_by='creation asc',)

        if len(faceids) < 4:
            # Delete old faceids
            for face in faceids:
                frappe.delete_doc('ESS Employee FaceID', face.name)
            frappe.db.commit()
            faceids = []
        elif len(faceids) > 4:
            if len(faceids) < 8:
                for i in range(len(faceids)):
                    if i > 3:
                        frappe.delete_doc('ESS Employee FaceID', faceids[i].name)
                frappe.db.commit()
                faceids = faceids[0:4]
            elif len(faceids) == 8:
                for i in range(len(faceids)):
                    if i <= 3:
                        frappe.delete_doc('ESS Employee FaceID', faceids[i].name)
                frappe.db.commit()
                faceids = faceids[4:]

        gen_response(200, i18n.t('translate.successfully',
                     locale=get_language()), faceids)
    except Exception as e:
        # message = e
        # gen_response(500, i18n.t('translate.error', locale=get_language()))
        exception_handel(e)


@frappe.whitelist(methods="POST")
def register_faceid_employee(**kwargs):
    doc_face_name = None
    doc_file_name = None

    settings = frappe.get_doc("ESS Employee Settings").as_dict()
    if not settings.get('api_key_face_ekgis'):
        return gen_response(404, i18n.t('translate.not_found_setting_face', locale=get_language()))

    try:
        employee_id = get_employee_id()
        faceimage = kwargs.get('faceimage')

        # check faceimage have string base64 ex: "data:image/jpeg;base64,"
        list_check = faceimage.split(",")
        if len(list_check) == 2:
            faceimage = list_check[1]

        # call api get vector
        url = f"https://api.ekgis.vn/deepvision/faceid/v1/encoding?api_key={settings.get('api_key_face_ekgis')}"
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({"faceimage": faceimage})

        response = requests.request(
            "POST", url, headers=headers, data=payload)

        # check response
        if response.status_code == 200:
            data = json.loads(response.text)
            if int(data.get('status')) == 4:
                gen_response(404, i18n.t(
                    'translate.not_face_recognition', locale=get_language()), {})
                return None

            # insert ESS Employee FaceID
            new_doc_face = frappe.new_doc("ESS Employee FaceID")
            new_doc_face.employee = employee_id
            new_doc_face.insert()
            doc_face_name = new_doc_face.get('name')

            # save file and insert Doctype File
            file_name = employee_id + "_" + str(datetime.now()) + "_.png"
            imgdata = base64.b64decode(faceimage)

            doc_file = save_file(file_name, imgdata, "ESS Employee FaceID", doc_face_name,
                                 folder=None, decode=False, is_private=0, df=None)

            # delete image copy
            path_file = "/files/" + file_name
            delete_file(path_file)

            # update ESS Employee FaceID
            doc_file_name = doc_file.get('name')
            base_url = frappe.utils.get_request_site_address()
            file_url = base_url + doc_file.get('file_url')
            doc_face = frappe.get_doc('ESS Employee FaceID', doc_face_name)
            doc_face.id_image = doc_file_name
            doc_face.url = file_url
            doc_face.image = file_url
            doc_face.vector = str(data.get("uploaded_faces"))
            doc_face.save()

            data = {}
            data['faceid_name'] = doc_face_name
            data['file_url'] = file_url

            gen_response(200, i18n.t(
                'translate.faceid_register_success', locale=get_language()), data)
            return None
        else:
            gen_response(404, i18n.t('translate.error', locale=get_language()))
            return None

    except Exception as e:
        # delete when error
        if doc_face_name:
            frappe.delete_doc('ESS Employee FaceID', doc_face_name)
        if doc_file_name:
            frappe.delete_doc('File', doc_file_name)

        message = e
        gen_response(500, i18n.t('translate.error', locale=get_language()))


@frappe.whitelist(methods="POST")
def update_faceid_employee(**kwargs):
    doc_file_name = None
    settings = frappe.get_doc("ESS Employee Settings").as_dict()
    if not settings.get('api_key_face_ekgis'):
        return gen_response(404, i18n.t('translate.not_found_setting_face', locale=get_language()))

    try:
        employee_id = get_employee_id()
        faceimage = kwargs.get('faceimage')
        doc_face_name = kwargs.get('faceid_name')

        # check doc exists
        check_faceid = frappe.db.exists("ESS Employee FaceID", doc_face_name)
        if not check_faceid:
            gen_response(404, i18n.t('translate.face_not_found',
                         locale=get_language()), [])
            return None

        # get doc
        doc_face = frappe.get_doc('ESS Employee FaceID', doc_face_name)
        id_image_old = doc_face.id_image

        # check faceimage have string base64 ex: "data:image/jpeg;base64,"
        list_check = faceimage.split(",")
        if len(list_check) == 2:
            faceimage = list_check[1]

        # call api get vector
        url = f"https://api.ekgis.vn/deepvision/faceid/v1/encoding?api_key={settings.get('api_key_face_ekgis')}"
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({"faceimage": faceimage})

        response = requests.request(
            "POST", url, headers=headers, data=payload)

        # check response
        if response.status_code == 200:
            data = json.loads(response.text)
            if int(data.get('status')) == 4:
                gen_response(404, i18n.t(
                    'translate.not_face_recognition', locale=get_language()), [])
                return None

            # save file and insert Doctype File
            file_name = employee_id + "_" + str(datetime.now()) + "_.png"
            imgdata = base64.b64decode(faceimage)
            doc_file_new = save_file(file_name, imgdata, "ESS Employee FaceID", doc_face_name,
                                     folder=None, decode=False, is_private=0, df=None)

            # delete image copy
            path_file = "/files/" + file_name
            delete_file(path_file)

            # update ESS Employee FaceID
            doc_file_name = doc_file_new.get('name')
            base_url = frappe.utils.get_request_site_address()
            file_url = base_url + doc_file_new.get('file_url')
            doc_face.id_image = doc_file_name
            doc_face.url = file_url
            doc_face.image = file_url
            doc_face.vector = str(data.get("uploaded_faces"))
            doc_face.save()

            # delete file old
            frappe.delete_doc('File', id_image_old)

            data = {}
            data['faceid_name'] = doc_face_name
            data['file_url'] = file_url

            gen_response(200, i18n.t('translate.faceid_success',
                         locale=get_language()), data)
            return None
        else:
            gen_response(404, i18n.t('translate.error', locale=get_language()))
    except Exception as e:
        # delete when error
        if doc_file_name:
            frappe.delete_doc('File', doc_file_name)

        gen_response(500, i18n.t('translate.error', locale=get_language()))


def add_text_to_image(file_name, imgdata, description):
    # add text to image
    # save image
    doc_file = save_file(file_name, imgdata, "", "",
                         folder=None, decode=False, is_private=0, df=None)
    # Open an Image
    path_file = frappe.get_site_path('public') + doc_file.file_url
    img = Image.open(path_file)
    # Lấy thông tin EXIF (nếu có)
    exif = img.info.get('exif')
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img)
    # Custom font style and font size
    default_font_size = 65
    font_path = os.path.dirname(__file__)
    font_relative_path = "../../font"
    font_directory = os.path.abspath(
        os.path.join(font_path, font_relative_path)) + "/FreeMono.ttf"

    myFont = ImageFont.truetype(font_directory, default_font_size)

    # myFont = ImageFont.load_default()
    # default_font_size = myFont.getsize("A")[0]

    # Add Text to an image
    lines = []
    x = 10
    y = 10
    max_width = img.width - (x + y)
    font_color = (255, 0, 0)
    for line in description.split("\n"):
        # Split line into words
        words = line.split()
        current_line = words[0]

        for word in words[1:]:
            # Check if adding the next word exceeds max_width
            if I1.textlength(current_line + " " + word, font=myFont) <= max_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)

    for line in lines:
        I1.text((x, y), line, font=myFont, fill=font_color)
        y += default_font_size
    # get image base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG", exif=exif)
    image_base64_new = base64.b64decode(base64.b64encode(buffered.getvalue()))

    # delete file
    frappe.delete_doc('File', doc_file.name)
    path_file = "/files/" + file_name
    delete_file(path_file)
    ##
    return image_base64_new


@frappe.whitelist(methods="POST")
def verify_faceid_employee(**kwargs):
    try:
        settings = frappe.get_doc("ESS Employee Settings").as_dict()
        api_key_face_ekgis = settings.get('api_key_face_ekgis')
        bucket_name_s3 = settings.get('bucket_name_s3')
        endpoint_s3 = settings.get('endpoint_s3')

        if not api_key_face_ekgis or not bucket_name_s3 or not endpoint_s3:
            return gen_response(404, i18n.t('translate.not_found_setting_face_s3', locale=get_language()))

        employee_id = get_employee_id()
        faceimage = kwargs.get('faceimage')
        description = str(kwargs.get('description'))

        # check faceimage have string base64 ex: "data:image/jpeg;base64,"
        list_check = faceimage.split(",")
        if len(list_check) == 2:
            faceimage = list_check[1]

        # get list vector employee register
        employee_faces = frappe.db.get_list("ESS Employee FaceID", filters={
            'employee': employee_id
        }, fields=['vector'])

        if not len(employee_faces):
            gen_response(404, i18n.t('translate.face_not_found',
                         locale=get_language()), [])
            return None

        # call api get vector
        url = f"https://api.ekgis.vn/deepvision/faceid/v1/encoding?api_key={api_key_face_ekgis}"
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({"faceimage": faceimage})

        response = requests.request(
            "POST", url, headers=headers, data=payload)
        print("========",response)
        if response.status_code == 200:
            data = json.loads(response.text)
            if int(data.get('status')) == 4:
                gen_response(404, i18n.t(
                    'translate.not_face_recognition', locale=get_language()), data)
                return None

            image_check = data.get("uploaded_faces")

            images_register = []
            for face in employee_faces:
                images_register.append(json.loads(face.get('vector')))
            # verify face
            check_verify = verify(image_check, images_register)
            if check_verify:
                imgdata = base64.b64decode(faceimage)
                file_name = "checkin_" + employee_id + \
                    "_" + str(datetime.now()) + ".png"

                if description:
                    imgdata_new = add_text_to_image(
                        file_name, imgdata, description)
                else:
                    imgdata_new = imgdata

                # imgdata_new = imgdata

                # save file image s3
                object_name = f"{frappe.local.site}/checkin/{file_name}"
                my_minio().put_object(bucket_name=bucket_name_s3,
                                    object_name=object_name, data=io.BytesIO(imgdata_new))

                # data response
                data = {}
                data["file_url"] = f"https://{endpoint_s3}/{bucket_name_s3}/{object_name}"
                data['status'] = True
                gen_response(200, i18n.t(
                    'translate.faceid_verify_success', locale=get_language()), data)
                return None
            else:
                data = {}
                data['status'] = False
                gen_response(200, i18n.t(
                    'translate.faceid_verify_fail', locale=get_language()), data)
                return None
        else:
            gen_response(404, i18n.t('translate.error', locale=get_language()))
    except Exception as e:
        print("==========",e)
        return exception_handel(e)
        
        # print(e)
        # gen_response(500, i18n.t('translate.error', locale=get_language()))

# End FaceID
