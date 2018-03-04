from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client


class FastDFSStorage(Storage):

    def __init__(self, client_conf=None, server_ip=None):

        if client_conf is None:

            client_conf = settings.CLIENT_CONF
        self.client_conf = client_conf

        if server_ip is None:
            server_ip = settings.SERVER_IP
        self.server_ip = server_ip


    def _open(self, name, mode='rb'):
        """打开文件时使用的:此处不是打开文件,而是存储文件到fdfs"""
        pass

    def _save(self, name, content):

        client = Fdfs_client(self.client_conf)

        file_data = content.read()

        try:

            ret = client.upload_appender_by_buffer(file_data)

        except Exception as e:

            print(e)

            raise
        """
        1. import fdfs_client.client module
        2. instantiate class Fdfs_client
        3. call memeber functions

        >>> from fdfs_client.client import *
        >>> client = Fdfs_client('/etc/fdfs/client.conf')
        >>> ret = client.upload_by_filename('test')
        >>> ret
        {'Group name':'group1','Status':'Upload successed.', 'Remote file_id':'group1/M00/00/00/
        	wKjzh0_xaR63RExnAAAaDqbNk5E1398.py','Uploaded size':'6.0KB','Local file name':'test'
        	, 'Storage IP':'192.168.243.133'}
        """

        if ret.get("Status") == 'Upload successed':

            File_id = ret.get('Remote file_id')
            return File_id
        else:

            raise Exception('上传失败')


    def exists(self, name):

        return False

    def url(self, name):
        return (self.server_ip + name)

    """
    1.创建client对象, 参数是 client.conf
    2.调用client.upload_by_bffer(file)
    3.接受返回值,内部包含了file_id
        ret = client.upload_by_bffer(file)
    4.存储file_id到mysql
    """