from flask import Flask, request, jsonify,json
import pymysql
import mysql.connector
import datetime
import base64
import binascii
import requests

app = Flask(__name__)
con=pymysql.connect(host="mysql-serv", user="root", password="root", db="selfielessacts")
cur=con.cursor()



# 3.Function to list number of acts in each category
@app.route('/api/v1/categories', methods=['GET'])
def list_categories():
	cur.execute("SELECT category, COUNT(DISTINCT actId) AS COUNT FROM acts GROUP BY category")
	ret=cur.fetchall()
	if(len(ret)==0):
		response = app.response_class(response=json.dumps({}), status=204, mimetype='application/json')
	else:
		d=dict()
		for i in ret:
			d[i['category']]=i['COUNT']
		response = jsonify(d)
	return response






# 4.Function to add a category
@app.route('/api/v1/categories', methods=['POST'])
def add_category():
	data=request.get_json()
	for category in data:
		cur.execute("SELECT COUNT(*) FROM categories WHERE category=%s", category)
		n=cur.fetchone()['COUNT(*)']
		if(n==0):
			query = ("INSERT INTO categories VALUES (%s)")
			input_data=(category)
			cur.execute(query, input_data)
			con.commit()
			response = app.response_class(response=json.dumps({}), status=201, mimetype='application/json')
		elif(n!=0):
			response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
	
	return response


# 5.Function to remove a category
@app.route('/api/v1/categories/<category>', methods=['DELETE'])
def rem_category(category):
	cur.execute("SELECT COUNT(*) FROM categories WHERE category=(%s)", category)
	n=cur.fetchone()['COUNT(*)']
	if(n==0):
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
	else:
		cur.execute("DELETE FROM acts WHERE category=(%s)", category)
		con.commit()
		cur.execute("DELETE FROM categories WHERE category=(%s)", category)
		con.commit()
		response = app.response_class(response=json.dumps({}), status=200, mimetype='application/json')
	return response


# 6 & 8.Function to list acts in a given category with optional range
@app.route('/api/v1/categories/<category>/acts', methods=['GET'])
def list_acts(category):
	cur.execute("SELECT COUNT(*) FROM categories WHERE category=(%s)", category)
	n=cur.fetchone()['COUNT(*)']
	if(n==0):
		response = app.response_class(response=json.dumps({}), status=204, mimetype='application/json')
		return response

	if(len(request.args)==0):
		cur.execute("SELECT COUNT(DISTINCT actId) FROM acts WHERE category=(%s)", category)
		n=cur.fetchone()['COUNT(DISTINCT actId)']
		if(n>100):
			response = app.response_class(response=json.dumps({}), status=413, mimetype='application/json')
			return response
		else:
			cur.execute("SELECT * FROM acts WHERE category=(%s)",category)
	else:
		start=int(request.args['start'])
		end=int(request.args['end'])
		cur.execute("SELECT COUNT(*) FROM acts WHERE category=(%s)", category)
		n=cur.fetchone()['COUNT(*)']

		if((end-start+1)>100):
			response = app.response_class(response=json.dumps({}), status=413, mimetype='application/json')
			return response
		elif(start<1 or end>n):
			response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
			return response
		else:
			cur.execute("SELECT * FROM acts ORDER BY time_stamp DESC LIMIT %s, %s", (start-1, end-start+1))
			
	json_list=list()
	json_array=list()
	json_array=cur.fetchall()
	for i in json_array:
		d=dict()
		d["actId"]=i["actId"]
		d["username"]=i["username"]
		k=str(i["time_stamp"])
		ss=k[17:19]
		mi=k[14:16]
		hh=k[11:13]
		dd=k[8:10]
		mm=k[5:7]
		yyyy=k[0:4]
		t=dd+"-"+mm+"-"+yyyy+":"+ss+"-"+mi+"-"+hh				

		d["timestamp"]=t
		d["caption"]=i["caption"]
		d["upvotes"]=i["likes"]
		d["imgB64"]=i["imgB64"]
		json_list.append(d)

	response = app.response_class(response=json.dumps(json_list), status=200, mimetype='application/json')
	return response



# 7.Function to return number of acts in a given category
@app.route('/api/v1/categories/<category>/acts/size', methods=['GET'])
def no_of_acts(category):
	cur.execute("SELECT COUNT(*) FROM categories WHERE category=(%s)", category)
	n=cur.fetchone()['COUNT(*)']
	if(n==0):
		response = app.response_class(response=json.dumps({}), status=204, mimetype='application/json')
	else:
		cur.execute("SELECT COUNT(*) FROM acts WHERE category=(%s)", category)
		n=cur.fetchone()['COUNT(*)']
		response = app.response_class(response=json.dumps([n]), status=200, mimetype='application/json')
	return response



# 9.Function to upvote
@app.route('/api/v1/acts/upvote', methods=['POST'])
def upvote():
	data=request.get_json()
	for actId in data:
		cur.execute("SELECT COUNT(*) FROM acts WHERE actId=(%s)", actId)
		n=cur.fetchone()['COUNT(*)']
		if(n==0):
			response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
		else:
			cur.execute("UPDATE acts SET likes=likes+1 WHERE actId=(%s)", actId)
			con.commit()
			response = app.response_class(response=json.dumps({}), status=200, mimetype='application/json')
	return response




# 10.Function to remove an act
@app.route('/api/v1/acts/<actId>', methods=['DELETE'])
def rem_act(actId):
	cur.execute("SELECT COUNT(*) FROM acts WHERE actId=(%s)", actId)
	n=cur.fetchone()['COUNT(*)']
	if(n==0):
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
	else:
		cur.execute("DELETE FROM acts WHERE actId=(%s)", actId)
		con.commit()
		response = app.response_class(response=json.dumps({}), status=200, mimetype='application/json')
	return response




# 11.Function to upload an act
@app.route('/api/v1/acts', methods=['POST'])
def upload_act():
	data=request.get_json()
	cur.execute("SELECT COUNT(*) FROM acts WHERE actId=(%s)", data['actId'])
	n=cur.fetchone()['COUNT(*)']
	if(n!=0):
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
		return response

	users=requests.get('http://127.0.0.1:8000/api/v1/users')
	if data['username'] in users:
		n=1
	else:
		n=0
	# cur.execute("SELECT COUNT(*) FROM users WHERE usn=(%s)", data['username'])
	# n=cur.fetchone()['COUNT(*)']
	if(n==0):
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
		return response

	def isBase64(s):
		try:
			base64.urlsafe_b64decode(s)
			return True
		except binascii.Error:
			return False

	if(not isBase64(data['imgB64'])):
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
		return response

	if(len(data)!=6):
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
		return response

	cur.execute("SELECT COUNT(*) FROM categories WHERE category=(%s)", data['categoryName'])
	n=cur.fetchone()['COUNT(*)']
	if(n==0):
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
		return response

	d=(data['timestamp'][0:2])
	m=(data['timestamp'][3:5])
	y=(data['timestamp'][6:10])
	s=(data['timestamp'][11:13])
	mi=(data['timestamp'][14:16])
	h=(data['timestamp'][17:19])
	
	try:
		query = ("INSERT INTO acts VALUES (\"%s\",\"%s\",'%s-%s-%s %s:%s:%s',\"%s\",\"%s\",\"%s\",0)"%(data['actId'], data['username'],y,m,d,h,mi,s,data['caption'], data['categoryName'], data['imgB64']))
		cur.execute(query)
		con.commit()
		response = app.response_class(response=json.dumps({}), status=201, mimetype='application/json')
	except:
		response = app.response_class(response=json.dumps({}), status=400, mimetype='application/json')
	return response






if __name__ == '__main__':
	app.run(port=80)
