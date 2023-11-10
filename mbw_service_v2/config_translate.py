import mbw_service_v2
import i18n
import os

base_file_path = os.path.dirname(mbw_service_v2.__file__)
i18n.load_path.append(base_file_path + '/translations')
