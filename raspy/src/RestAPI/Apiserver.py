import werkzeug
import os
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from sqlalchemy import create_engine
from json import dumps
from flask_jsonpify import jsonify
import imp
db = imp.load_source('DBWrapper', '../Database/DBWrapper.py')
dbw = db.DBWrapper()
import base64
cv2wrapper = imp.load_source('CV2Wrapper', '../ComputerVision/CV2Wrapper.py')
faceDetector = imp.load_source('FaceDetector', '../ComputerVision/FaceDetector.py')

# db_connect = create_engine('sqlite:///tmp/TrackingCollection.db')
app = Flask(__name__)
api = Api(app)

parserUpload = reqparse.RequestParser()
parserUpload.add_argument('uploadFile', type=werkzeug.datastructures.FileStorage, location='files')
parserUpload.add_argument('name')

class LocationHistorySRPL(Resource):
    def get(self, face_id):
        # conn = db_connect.connect()
        # query = conn.execute("select * FROM locationHistory WHERE face_id = %d " %int(face_id))
        # result = {'data': [dict(zip(tuple (query.keys()) ,i)) for i in query.cursor]}
        result = dbw.getLocationsOf(face_id)
        return { 'data': result}, 200, {'Access-Control-Allow-Origin': '*'}
        
class FaceBankSRPL(Resource):
    def options(self):
        return {'Allow' : 'POST' }, 200, \
               { 'Access-Control-Allow-Origin': '*', \
                'Access-Control-Allow-Methods' : 'PUT,GET' }
    def post(self):
        args = parserUpload.parse_args()
        path = os.getcwd() + "/SRPL/" + args['uploadFile'].filename
        args['uploadFile'].save(path);
        name = args['name']
        faced = faceDetector.FaceDetector()
        cv2 = cv2wrapper.CV2Wrapper()
        with open(path, "rb") as image_file:
            data = image_file.read()
        faces = []
        faces = faces + [cv2.imageToBinary(face) for face in faced.detectFromBinary(data)]
        print "Detected %d faces" % len(faces)
        ids = []
        number = 1
        for found in faces:
            filename = 'SRPL/%s_%d.jpg' % (args['uploadFile'].filename, number)
            with open(filename, 'wb') as f:
                f.write(found)
            lastId = dbw.insertNewFaceImage(name, os.getcwd() + '/' + filename, 0)
            ids.append(lastId)
            number = number + 1
        os.remove(path)
        return {'ids': ids}, 201, {'Access-Control-Allow-Origin': '*'}
    
    def get(self):
        result = dbw.getFaces(0)
        i = 0
        for var in result:
            with open(var[1], "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
            new = (var[0], encoded_string, var[2])
            result[i] = new
            i += 1
        return { 'data': result}, 200, {'Access-Control-Allow-Origin': '*'}

api.add_resource(FaceBankSRPL, '/faces/srpl')
api.add_resource(LocationHistorySRPL, '/locations/srpl/<face_id>')


if __name__ == '__main__':
     app.run(host= '172.17.0.2', port='5200')