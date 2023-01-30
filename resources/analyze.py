from flask_restful import Resource, reqparse
from flask import request, jsonify
from security import api_required

import tensorflow as tf
tf_version = int(tf.__version__.split(".")[0])
import uuid
import json
import time
from tqdm import tqdm
#------------------------------

if tf_version == 2:
	import logging
	tf.get_logger().setLevel(logging.ERROR)

#------------------------------

from deepface import DeepFace

class ImageAnalyzer(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('img',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )

    @api_required
    def post(self):        
        response = self.analyze()
        return response        


    def analyzeWrapper(self, req, trx_id = 0):
            resp_obj = jsonify({'success': False})

            instances = []
            if "img" in list(req.keys()):
                raw_content = req["img"] #list

                for item in raw_content: #item is in type of dict
                    instances.append(item)

            if len(instances) == 0:
                return jsonify({'success': False, 'error': 'you must pass at least one img object in your request'}), 205

            print("Analyzing ", len(instances)," instances")

            #---------------------------

            detector_backend = 'opencv'

            actions= ['emotion', 'age', 'gender', 'race']

            if "actions" in list(req.keys()):
                actions = req["actions"]

            if "detector_backend" in list(req.keys()):
                detector_backend = req["detector_backend"]

            #---------------------------

            try:
                resp_obj = DeepFace.analyze(instances, actions = actions)
            except Exception as err:
                print("Exception: ", str(err))
                return jsonify({'success': False, 'error': str(err)}), 205

            #---------------
            #print(resp_obj)
            return resp_obj


    def analyze(self):

        global graph

        tic = time.time()
        req = request.get_json()
        trx_id = uuid.uuid4()

        #---------------------------

        if tf_version == 1:
            with graph.as_default():
                resp_obj = self.analyzeWrapper(req, trx_id)
        elif tf_version == 2:
            resp_obj = self.analyzeWrapper(req, trx_id)

        #---------------------------

        toc = time.time()

        resp = {}

        resp["trx_id"] = str(trx_id)
        resp["seconds"] = toc-tic

        if isinstance(resp_obj, list):
            for idx, instance in enumerate(resp_obj):
                resp[f"instance_{idx+1}"] = instance
        elif isinstance(resp_obj, dict):
            resp["instance_1"] = resp_obj

        return resp, 200

    