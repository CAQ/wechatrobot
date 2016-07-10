#!/usr/bin/env python
# coding=utf-8

'''
登录过程、群组操作源自：
https://github.com/0x5e/wechat-deleted-friends
心跳参考自：
http://reverland.org/javascript/2016/01/15/webchat-user-bot/
'''

from answer import GetAnswer

import os
import urllib, urllib2
import re
import cookielib
import time, datetime
import json
import sys
import math
import xml.dom.minidom

DEBUG = True

QRImagePath = os.getcwd() + '/qrcode.jpg'

tip = 0
uuid = ''

base_uri = ''
redirect_uri = ''

skey = ''
wxsid = ''
wxuin = ''
pass_ticket = ''
deviceId = 'e000000000000000'

BaseRequest = {}

ContactList = []
My = []

def getUUID():
	global uuid

	url = 'https://login.weixin.qq.com/jslogin'
	params = {
		'appid': 'wx782c26e4c19acffb',
		'fun': 'new',
		'lang': 'zh_CN',
		'_': int(time.time()),
	}

	request = urllib2.Request(url = url, data = urllib.urlencode(params))
	response = urllib2.urlopen(request)
	data = response.read()

	# print data

	# window.QRLogin.code = 200; window.QRLogin.uuid = "xxxx_xxxxx==";
	regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
	pm = re.search(regx, data)

	code = pm.group(1)
	uuid = pm.group(2)

	if code == '200':
		return True

	return False

def showQRImage():
	global tip
	print '正在下载二维码图片...'

	url = 'https://login.weixin.qq.com/qrcode/' + uuid
	params = {
		't': 'webwx',
		'_': int(time.time()),
	}

	request = urllib2.Request(url = url, data = urllib.urlencode(params))
	response = urllib2.urlopen(request)

	tip = 1

	f = open(QRImagePath, 'wb')
	f.write(response.read())
	f.close()

	#if sys.platform.find('darwin') >= 0:
	#	os.system('open %s' % QRImagePath)
	#elif sys.platform.find('linux') >= 0:
	#	os.system('xdg-open %s' % QRImagePath)
	#else:
	#	os.system('call %s' % QRImagePath)
	#print '请使用微信扫描二维码以登录'

	print '请访问本地的 qrcode.jpg 扫描二维码以登录'

def waitForLogin():
	global tip, base_uri, redirect_uri

	url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (tip, uuid, int(time.time()))

	request = urllib2.Request(url = url)
	response = urllib2.urlopen(request)
	data = response.read()
	
	# print data

	# window.code=500;
	regx = r'window.code=(\d+);'
	pm = re.search(regx, data)

	code = pm.group(1)

	if code == '201': #已扫描
		print '成功扫描,请在手机上点击确认以登录'
		tip = 0
	elif code == '200': #已登录
		print '正在登录...'
		regx = r'window.redirect_uri="(\S+?)";'
		pm = re.search(regx, data)
		redirect_uri = pm.group(1) + '&fun=new'
		base_uri = redirect_uri[:redirect_uri.rfind('/')]
	elif code == '408': #超时
		pass
	# elif code == '400' or code == '500':

	return code

def login():
	global skey, wxsid, wxuin, pass_ticket, BaseRequest

	request = urllib2.Request(url = redirect_uri)
	response = urllib2.urlopen(request)
	data = response.read()

	# print data

	'''
		<error>
			<ret>0</ret>
			<message>OK</message>
			<skey>xxx</skey>
			<wxsid>xxx</wxsid>
			<wxuin>xxx</wxuin>
			<pass_ticket>xxx</pass_ticket>
			<isgrayscale>1</isgrayscale>
		</error>
	'''

	doc = xml.dom.minidom.parseString(data)
	root = doc.documentElement

	for node in root.childNodes:
		if node.nodeName == 'skey':
			skey = node.childNodes[0].data
		elif node.nodeName == 'wxsid':
			wxsid = node.childNodes[0].data
		elif node.nodeName == 'wxuin':
			wxuin = node.childNodes[0].data
		elif node.nodeName == 'pass_ticket':
			pass_ticket = node.childNodes[0].data

	# print 'skey: %s, wxsid: %s, wxuin: %s, pass_ticket: %s' % (skey, wxsid, wxuin, pass_ticket)

	if skey == '' or wxsid == '' or wxuin == '' or pass_ticket == '':
		return False

	BaseRequest = {
		'Uin': int(wxuin),
		'Sid': wxsid,
		'Skey': skey,
		'DeviceID': deviceId,
	}

	return True

SyncKey = None
def webwxinit():

	url = base_uri + '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (pass_ticket, skey, int(time.time()))
	params = {
		'BaseRequest': BaseRequest
	}

	request = urllib2.Request(url = url, data = json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()

	if DEBUG == True:
		f = open(os.getcwd() + '/webwxinit.json', 'wb')
		f.write(data)
		f.close()

	# print data

	global ContactList, My, SyncKey
	dic = json.loads(data)
	ContactList = dic['ContactList']
	My = dic['User']
	SyncKey = dic['SyncKey']

	ErrMsg = dic['BaseResponse']['ErrMsg']
	if len(ErrMsg) > 0:
		print ErrMsg

	Ret = dic['BaseResponse']['Ret']
	if Ret != 0:
		return False
		
	return True


NameMap = {}
def webwxgetcontact():
	global NameMap
	print '正在读取联系人...'
	
	url = base_uri + '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (pass_ticket, skey, int(time.time()))

	request = urllib2.Request(url = url)
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()

	if DEBUG == True:
		f = open(os.getcwd() + '/webwxgetcontact.json', 'wb')
		f.write(data)
		f.close()

	# print data

	dic = json.loads(data)
	MemberList = dic['MemberList']

	# 倒序遍历,不然删除的时候出问题..
	SpecialUsers = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail', 'fmessage', 'tmessage', 'qmessage', 'qqsync', 'floatbottle', 'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 'readerapp', 'blogapp', 'facebookapp', 'masssendapp', 'meishiapp', 'feedsapp', 'voip', 'blogappweixin', 'weixin', 'brandsessionholder', 'weixinreminder', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'officialaccounts', 'notification_messages', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'wxitil', 'userexperience_alarm', 'notification_messages']
	for i in xrange(len(MemberList) - 1, -1, -1):
		Member = MemberList[i]
		nickname = Member['NickName']
		if type(nickname) is unicode:
			nickname = nickname.encode('utf-8')
		NameMap[Member['UserName']] = nickname
		if Member['VerifyFlag'] & 8 != 0: # 公众号/服务号
			MemberList.remove(Member)
		elif Member['UserName'] in SpecialUsers: # 特殊账号
			MemberList.remove(Member)
		#elif Member['UserName'].find('@@') != -1: # 群聊
		#	MemberList.remove(Member)
		#elif Member['UserName'] == My['UserName']: # 自己
		#	MemberList.remove(Member)

	return MemberList

def createChatroom(UserNames):
	MemberList = []
	for UserName in UserNames:
		MemberList.append({'UserName': UserName})


	url = base_uri + '/webwxcreatechatroom?pass_ticket=%s&r=%s' % (pass_ticket, int(time.time()))
	params = {
		'BaseRequest': BaseRequest,
		'MemberCount': len(MemberList),
		'MemberList': MemberList,
		'Topic': '',
	}

	request = urllib2.Request(url = url, data = json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()

	# print data

	dic = json.loads(data)
	ChatRoomName = dic['ChatRoomName']
	MemberList = dic['MemberList']
	DeletedList = []
	for Member in MemberList:
		if Member['MemberStatus'] == 4: #被对方删除了
			DeletedList.append(Member['UserName'])

	ErrMsg = dic['BaseResponse']['ErrMsg']
	if len(ErrMsg) > 0:
		print ErrMsg

	return (ChatRoomName, DeletedList)

def deleteMember(ChatRoomName, UserNames):
	url = base_uri + '/webwxupdatechatroom?fun=delmember&pass_ticket=%s' % (pass_ticket)
	params = {
		'BaseRequest': BaseRequest,
		'ChatRoomName': ChatRoomName,
		'DelMemberList': ','.join(UserNames),
	}

	request = urllib2.Request(url = url, data = json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()

	# print data

	dic = json.loads(data)
	ErrMsg = dic['BaseResponse']['ErrMsg']
	if len(ErrMsg) > 0:
		print ErrMsg

	Ret = dic['BaseResponse']['Ret']
	if Ret != 0:
		return False
		
	return True

def addMember(ChatRoomName, UserNames):
	url = base_uri + '/webwxupdatechatroom?fun=addmember&pass_ticket=%s' % (pass_ticket)
	params = {
		'BaseRequest': BaseRequest,
		'ChatRoomName': ChatRoomName,
		'AddMemberList': ','.join(UserNames),
	}

	request = urllib2.Request(url = url, data = json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()

	# print data

	dic = json.loads(data)
	MemberList = dic['MemberList']
	DeletedList = []
	for Member in MemberList:
		if Member['MemberStatus'] == 4: #被对方删除了
			DeletedList.append(Member['UserName'])

	ErrMsg = dic['BaseResponse']['ErrMsg']
	if len(ErrMsg) > 0:
		print ErrMsg

	return DeletedList


GroupMap = {}
def webwxbatchgetcontact():
	global NameMap, GroupMap
	grouplist = []
	for username in NameMap:
		if username.find('@@') == 0:
			grouplist.append({'UserName':username, 'EncryChatRoomId':''})

	r = str(long(time.time() * 1000))
	url = base_uri + '/webwxbatchgetcontact?lang=zh_CN&type=ex&r=%s&pass_ticket=%s' % (r, pass_ticket)
	params = {
		'BaseRequest': BaseRequest,
		'List': grouplist,
		'Count': len(grouplist)
	}

	request = urllib2.Request(url = url, data = json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()

	if DEBUG == True:
		f = open(os.getcwd() + '/webwxbatchgetcontact.json', 'wb')
		f.write(data)
		f.close()

	dic = json.loads(data)
	contactlist = dic['ContactList']
	for contact in contactlist:
		GroupMap[contact['UserName']] = contact

	return GroupMap



#import requests
def webwxsendmsg(content, touser):
	global MyUserName

	if type(content) is str:
		content = content.decode('utf-8')
	url = base_uri + '/webwxsendmsg?lang=zh_CN&pass_ticket=%s' % (pass_ticket)
	msgid = str(long(time.time() * 1000)) + '1481'
	params = {
		'BaseRequest': BaseRequest,
		'Msg': {
			'ClientMsgId': msgid,
			'LocalID': msgid,
			'Content': content,
			'FromUserName': MyUserName,
			'ToUserName': touser,
			'Type': 1
		}
	}
	senddata = json.dumps(params, ensure_ascii=False) # 'unicode' type
	
	request = urllib2.Request(url = url, data = senddata.encode('utf-8'))
	request.add_header('Content-Type', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()
	#r = requests.post(url, data=senddata.decode('utf-8'), headers={'Content-Type':'application/json; charset=UTF-8'})
	#data = r.content

	if DEBUG == True:
		f = open(os.getcwd() + '/webwxsendmsg.json', 'wb')
		f.write(data)
		f.close()

	return json.loads(data)


# POST
def webwxsync():
	global SyncKey
	url = base_uri + '/webwxsync?sid=%s&skey=%s&pass_ticket=%s' % (wxsid, skey, pass_ticket)

	if SyncKey is None:
		print 'No SyncKey'
		return
	SyncKey['rr'] = ~(int(time.time() * 1000))
	params = {
		'BaseRequest': BaseRequest,
		'SyncKey': SyncKey
	}

	request = urllib2.Request(url = url, data = json.dumps(params))
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()

	if DEBUG == True:
		f = open(os.getcwd() + '/webwxsync.json', 'wb')
		f.write(data)
		f.close()

	return json.loads(data)


# GET
def synccheck():
	global SyncKey
	if SyncKey is None:
		print 'No SyncKey'
		return

	synckeystr = '%7C'.join([str(sk['Key']) + '_' + str(sk['Val']) for sk in SyncKey['List']])

	url = 'https://webpush.weixin.qq.com/cgi-bin/mmwebwx-bin/synccheck?r=%s&skey=%s&sid=%s&uin=%s&deviceid=%s&synckey=%s' % (int(time.time() * 1000), skey, wxsid, wxuin, deviceId, synckeystr)

	request = urllib2.Request(url = url)
	request.add_header('ContentType', 'application/json; charset=UTF-8')
	response = urllib2.urlopen(request)
	data = response.read()
	print data

	if DEBUG == True:
		f = open(os.getcwd() + '/synccheck.json', 'wb')
		f.write(data)
		f.close()

	# window.synccheck={retcode:"0",selector:"2"}
	data = data[data.find('{') : data.rfind('}') + 1]
	data = data.replace('retcode', '"retcode"').replace('selector', '"selector"')
	return json.loads(data)


def ProcessMsgs(msglist):
	global NameMap, MyUserName, GroupMap
	for msg in msglist:
		content = msg['Content']
		if content is None:
			continue
		if type(content) is str:
			content = content.decode('utf-8')
		# Post this msg
		#print content
		if msg['FromUserName'].find('@@') == 0:
			# Some other posted to a group, still post into this group
			willtouser = msg['FromUserName']
			if content.find('@') == 0:
				pos1 = content.find(':')
				pos2 = content.find('<br/>', pos1) + 5
				atuser = content[ : pos1]
				content = content[pos2 : ]
				groupname = msg['FromUserName']
				if groupname in GroupMap:
					for member in GroupMap[groupname]['MemberList']:
						if member['UserName'] == atuser:
							atuser = member['DisplayName']
				if atuser in NameMap:
					atuser = NameMap[atuser]
			else:
				atuser = None
		elif msg['ToUserName'].find('@@') == 0:
			# I posted to a group
			atuser = None
			groupname = msg['ToUserName']
			if groupname in GroupMap:
				for member in GroupMap[groupname]['MemberList']:
					if member['UserName'] == MyUserName:
						atuser = member['DisplayName']
			if atuser is None and MyUserName in NameMap:
				atuser = NameMap[MyUserName]
			willtouser = msg['ToUserName']
		else:
			# Some other to me, reply to that person
			willtouser = msg['FromUserName']
			atuser = None
		# Answer this msg
		answer = GetAnswer(content)

		# If None, continue (no response).
		if answer is None or len(answer.strip()) == 0:
			continue

		# Add the user's nickname
		if atuser is not None:
			answer = '@' + atuser + ' ' + answer
		response = webwxsendmsg(answer, willtouser)
		if response['BaseResponse']['Ret'] != 0:
			print '发送失败:', response['BaseResponse']['ErrMsg'], content, answer
		else:
			print response['MsgID'], content, answer
		time.sleep(0.5)

MyUserName = None
def main():
	global SyncKey, MyUserName, myselfconfig

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
	urllib2.install_opener(opener)
	
	if getUUID() == False:
		print '获取uuid失败'
		return

	showQRImage()
	time.sleep(1)

	while waitForLogin() != '200':
		pass

	os.remove(QRImagePath)

	if login() == False:
		print '登录失败'
		return

	if webwxinit() == False:
		print '初始化失败'
		return

	MemberList = webwxgetcontact()
	MemberCount = len(MemberList)
	print '通讯录共%s位好友' % MemberCount

	groupmap = webwxbatchgetcontact()
	print '通讯录共%s个群组' % len(groupmap)

	# Get my username
	for user in MemberList:
		thisUser = True
		for key in myselfconfig:
			if key not in user or user[key] != myselfconfig[key]:
				thisUser = False
				break
		if thisUser:
			MyUserName = user['UserName']
			break
	if MyUserName is None:
		print '获取主账号信息失败'
		return

	webwxsendmsg('机器人已连接：' + str(datetime.datetime.now()), MyUserName)

	# Monitor new messages
	print '开始监听新消息'
	idlecount = 0
	idleintervalseconds = 3
	while True:
		synccheckdata = synccheck()
		if synccheckdata['retcode'] != 0 or synccheckdata['selector'] != 0:
			syncdata = webwxsync()
			SyncKey = syncdata['SyncKey']
			if syncdata['AddMsgCount'] > 0:
				print '收到%s条消息' % syncdata['AddMsgCount']
				ProcessMsgs(syncdata['AddMsgList'])
				idlecount = 0
		time.sleep(idleintervalseconds)





# windows下编码问题修复
# http://blog.csdn.net/heyuxuanzee/article/details/8442718
class UnicodeStreamFilter:  
	def __init__(self, target):  
		self.target = target  
		self.encoding = 'utf-8'  
		self.errors = 'replace'  
		self.encode_to = self.target.encoding  
	def write(self, s):  
		if type(s) == str:  
			s = s.decode('utf-8')  
		s = s.encode(self.encode_to, self.errors).decode(self.encode_to)  
		self.target.write(s)  
		  
if sys.stdout.encoding == 'cp936':  
	sys.stdout = UnicodeStreamFilter(sys.stdout)

myselfconfig = {}
if __name__ == '__main__' :

	try:
		with open('myself.config') as f:
			for line in f:
				fields = line.strip().split('=', 1)
				if len(fields) != 2:
					continue
				myselfconfig[fields[0]] = fields[1]
		if len(myselfconfig) == 0:
			print 0/0
	except:
		print '主账号信息配置失败'
		raise
				

	reload(sys)
	sys.setdefaultencoding('utf-8')




	#print '本程序的查询结果可能会引起一些心理上的不适,请小心使用...'
	#print '回车键继续...'
	#raw_input()

	main()

	print '回车键结束'
	raw_input()
