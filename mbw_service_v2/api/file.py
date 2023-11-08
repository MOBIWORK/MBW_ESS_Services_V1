import frappe
from minio import Minio
import numpy as np
from scipy.spatial.distance import cdist


class MinioConnection:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, region: str, secure: bool):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            secure=secure,
        )

    def validate_bucket(self, bucket_name: str):
        try:
            if self.client.bucket_exists(bucket_name):
                frappe.msgprint(_("Great! Bucket is accesible ;)"),
                                indicator="green", alert=True)
                return True
            else:
                frappe.throw(_("Bucket not found"))
        except Exception as e:
            if hasattr(e, "message"):
                frappe.throw(
                    _("Error when looking for bucket: {}".format(e.message)))
            elif hasattr(e, "reason"):
                frappe.throw(str(e))
        return False

    def remove_object(self, bucket_name: str, object_name: str):
        """
        Minio params:
        :param bucket_name: Name of the bucket.
        :param object_name: Object name in the bucket.
        :param version_id: Version ID of the object.
        """
        return self.client.remove_object(bucket_name=bucket_name, object_name=object_name)

    def get_object(self, bucket_name: str, object_name: str):
        """
        Minio params:
        :param bucket_name: Name of the bucket.
        :param object_name: Object name in the bucket.
        :param offset: Start byte position of object data.
        :param length: Number of bytes of object data from offset.
        :param request_headers: Any additional headers to be added with GET request.
        :param ssec: Server-side encryption customer key.
        :param version_id: Version-ID of the object.
        :param extra_query_params: Extra query parameters for advanced usage.
        :return: :class:`urllib3.response.HTTPResponse` object.
        """

        return self.client.get_object(bucket_name=bucket_name, object_name=object_name)

    def put_object(self, bucket_name, object_name, data,
                   metadata={'x-amz-acl': 'public-read'}, length=-1, part_size=10 * 1024 * 1024):
        """
        Minio params:
        :param bucket_name: Name of the bucket.
        :param object_name: Object name in the bucket.
        :param data: An object having callable read() returning bytes object.
        :param length: Data size; -1 for unknown size and set valid part_size.
        :param content_type: Content type of the object.
        :param metadata: Any additional metadata to be uploaded along
                with your PUT request.
        :param sse: Server-side encryption.
        :param progress: A progress object;
        :param part_size: Multipart part size.
        :param num_parallel_uploads: Number of parallel uploads.
        :param tags: :class:`Tags` for the object.
        :param retention: :class:`Retention` configuration object.
        :param legal_hold: Flag to set legal hold for the object.
        """

        return self.client.put_object(bucket_name=bucket_name,
                                      object_name=object_name, data=data, metadata=metadata,
                                      length=length, part_size=part_size)

def create_my_minio():
    settings = frappe.get_doc("MBW Employee Settings").as_dict()

    return MinioConnection(
        endpoint=settings.get("endpoint_s3"),
        access_key=settings.get("access_key_s3"),
        secret_key=settings.get("key_secret_s3"),
        region="auto",
        secure=0
    )
    
my_minio = create_my_minio()


def distance_cal(embedding_check, know_embedding):
    distances = cdist(embedding_check, know_embedding, 'cosine')
    return distances


def verify(embedding_check, know_embedding, threshsold=0.5):
    distances = distance_cal([embedding_check], know_embedding)
    distances = np.array(distances)
    mask = distances < threshsold
    if True in mask:
        return True
    else:
        return False
