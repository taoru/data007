'''
Created by auto_sdk on 2013-04-01 16:44:41
'''
from top.api.base import RestApi
class RefundGetRequest(RestApi):
	def __init__(self,domain='gw.api.taobao.com',port=80):
		RestApi.__init__(self,domain, port)
		self.fields = None
		self.refund_id = None

	def getapiname(self):
		return 'taobao.refund.get'
