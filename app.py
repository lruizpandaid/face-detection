import warnings
warnings.filterwarnings("ignore")

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from flask import Flask, request, jsonify, make_response

import uuid
import json
import time
from tqdm import tqdm

#------------------------------

import tensorflow as tf
tf_version = int(tf.__version__.split(".")[0])

#------------------------------

if tf_version == 2:
	import logging
	tf.get_logger().setLevel(logging.ERROR)

#------------------------------

from deepface import DeepFace


app = Flask(__name__)


@app.route("/")
def hello_from_root():
    return jsonify(message='Hello from root!')


@app.route("/hello")
def hello():
    return jsonify(message='Hello from path!')


@app.errorhandler(404)
def resource_not_found(e):
    return make_response(jsonify(error='Not found!'), 404)

@app.route('/analyze', methods=['POST'])
def analyze():

	global graph

	tic = time.time()
	req = request.get_json()
	trx_id = uuid.uuid4()

	#---------------------------

	if tf_version == 1:
		with graph.as_default():
			resp_obj = analyzeWrapper(req, trx_id)
	elif tf_version == 2:
		resp_obj = analyzeWrapper(req, trx_id)

	#---------------------------

	toc = time.time()

	resp = {}

	resp["trx_id"] = trx_id
	resp["seconds"] = toc-tic

	if isinstance(resp_obj, list):
		for idx, instance in enumerate(resp_obj):
			resp[f"instance_{idx+1}"] = instance
	elif isinstance(resp_obj, dict):
		resp["instance_1"] = resp_obj

	return resp, 200

def analyzeWrapper(req, trx_id = 0):
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

if __name__ == '__main__':
	app.run()
