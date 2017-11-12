import httplib, urllib, requests, os, json
from base64 import b64encode

class AEMTools:

    _protocol = "http"
    _server = ""
    _user = ""
    _passwd = ""
    _testPath = "/system/console/bundles"
    _isconnected = False
    _authHeader = ""


    def __init__(self, server,user, passwd):

        if server[:4] == "http":
            self._protocol = "http"
            self._server = server[7:]

        elif server[:5] == "https":
            self._protocol = "https"
            self._server = server[8:]

        self._user = user
        self._passwd = passwd

        userAndPass = b64encode(b""+self._user+":"+self._passwd).decode("ascii")
        self._authHeader = {'Authorization': 'Basic %s' % userAndPass}

        self.testConnection()


    def generateConection(self,url=False):
        if url is False:
            url = self._server
        if self._protocol == "http":
            conn = httplib.HTTPConnection(url)
        elif self._protocol == "https":
            conn = httplib.HTTPSConnection(url)
        return conn

    def testConnection(self):

        conn = self.generateConection()
        conn.request("GET", self._testPath, headers=self._authHeader)
        r1 = conn.getresponse()
        if r1.status is 200:
            self._isconnected = True
        else:
            self._isconnected = False

    def isConnected(self):
        return self._isconnected

    def sanitizeURL(self,url):
        line = ""
        if url[:1] == "/":
            url = url[1:]

        for kv in url.split("/"):
            line = line + "/" + urllib.quote(kv)

        return line

    def getNodeJson(self,dir):
        if self._isconnected:
            response = requests.get(self._protocol+ "://"+self._server+self.sanitizeURL(dir)+".json", headers=self._authHeader)

            if response.status_code is 200:
                obj = json.loads(response.text)
                status = {"status":"ok","text": obj }
            else:
                status = {"status": "error", "text": "Error "+str(response.status_code)}
            return status

    def isSlingFolder(self,dir):
        check = self.getNodeJson(dir)
        if check["status"] == "ok":
            body = check["text"]
            if body["jcr:primaryType"] == "sling:OrderedFolder" or body["jcr:primaryType"] == "sling:Folder":
                return True
        return False


    def createDir(self,dir):
        if self._isconnected:
            conn = self.generateConection()
            conn.request("MKCOL", self.sanitizeURL(dir), headers=self._authHeader)
            response = conn.getresponse()
            conn.close()

            status = {}
            if response.status is 201:
                status = {"status":"ok","text": dir}
            else:
                if self.isSlingFolder(dir):
                    status = {"status": "ok", "text": dir}
                else:
                    status = {"status": "error", "text": "Error "+str(response.status)+": '"+response.reason+"' while creating Directory: "+dir}
            return status

    def deleteNode(self,dir):
        if self._isconnected:
            payload = {':operation':'delete'}
            r = requests.post(self._protocol+ "://"+self._server+self.sanitizeURL(dir), data=payload, headers=self._authHeader)

            status = {}
            if r.status_code is 200:
                status = {"status":"ok","text": dir}
            else:
                node = self.getNodeJson(dir=dir)
                if node["text"] == 'Error 404':
                    status = {"status": "notfound", "text": "Notice: 404 while deleting node: "+dir}
                else:
                    status = {"status": "error", "text": "Error "+str(r.status_code)+": while deleting node: "+dir}
            return status


    def uploadFile(self,fsFile,repoFile):
        if self._isconnected:

            dirPart = os.path.dirname(repoFile)
            filenPart = os.path.basename(repoFile)

            files = {
                filenPart: open(fsFile, 'rb')
            }

            r = requests.post(self._protocol+ "://"+self._server+self.sanitizeURL(dirPart), files=files, headers=self._authHeader )

            status = {}
            if r.status_code is 200:
                status = {"status":"ok","text": repoFile}
            else:
                status = {"status": "error", "text": "Error "+str(r.status_code)+": while creating Fike: "+repoFile}
            return status







# Sample on how to use headers with hhtplib
# headers = {
#     "Content-type": "multipart/form-data",
#     "Accept": "text/plain"
# }
# headers.update(self._authHeader)
#
# conn = self.generateConection()
#
# # https://stackoverflow.com/questions/3079562/upload-a-file-with-python-using-httplib
# conn.request("POST", self.sanitizeURL(repoFile), open(fsFile, "rb"), headers=headers)
# response = conn.getresponse()
# #remote_file = response.read()
# print response.status
# conn.close()
#
# # print remote_file
#
#
#
