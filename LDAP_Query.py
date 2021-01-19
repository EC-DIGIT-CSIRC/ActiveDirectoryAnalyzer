#!/usr/bin/env python3
# encoding: utf-8

from cortexutils.analyzer import Analyzer
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES
import json

class LDAPAnalyzer(Analyzer):

	#Handle configuration file options
	def __init__(self):
		Analyzer.__init__(self)
		self.ldap_server = self.get_param('config.server', None, 'LDAP server is missing')
		self.bind_username = self.get_param('config.bind_username', None, 'Account is missing')
		self.bind_password = self.get_param('config.bind_password', None, 'Password is missing')
		self.base = self.get_param('config.baseDN', None, 'BaseDN is missing')
		self.service = self.get_param('config.service', None, 'Service parameter is missing')
		self.query = "(sAMAccountName=%s)" % self.get_data()
	
	#Make binding to LDAP
	def connect(self):
		try:
			self.server = Server(self.ldap_server, get_info=ALL)
			self.connection = Connection(self.server, self.bind_username, self.bind_password, auto_bind=True) 
		except Exception as e:
			self.error(e)
	
	#Make LDAP query
	def search(self):
		try:
			self.connection.search(self.base, self.query, attributes=[ALL_ATTRIBUTES])
		except Exception as e:
			self.error(e)
	
	#Put all members in self member variable
	def group_members(self):
		if self.connection.entries[0]['member']:
			self.members = {}
			self.members['members'] = self.connection.entries[0]['member'].value
		else:
			self.error("member attribute is not defined")
	
	#Generate Short report
	def summary(self, raw):
		taxonomies = []
		namespace = "LDAP"
		value = "\"0\""
		result = {
			"has_result": True
		}
		
		if self.service == 'ldap-user':
			predicate = "Attributes"
			#If no result then return an error
			if not self.connection.entries[0]:
				result["has_result"] = False
			else:
				level = "info"
				value = "{}".format(len(vars(self.connection.entries[0]).items()))
		elif self.service == 'ldap-group':
			predicate = "Members"
			#If no result then return an error
			if not self.members:
				result["has_result"] = False
			else:
				level = "info"
				value = "{}".format(len(self.members))
		
		#Build taxonomy
		taxonomies.append(self.build_taxonomy(level, namespace, predicate, value))
		return {"taxonomies": taxonomies}

	#Analyzer main function
	def run(self):
		if (self.bind_username is None) or (self.bind_password is None) or (self.ldap_server is None) or (self.base is None):
			self.error('Invalid configuration')
		else:
			if self.service == 'ldap-user':
				self.connect()
				self.search()
				self.report(json.loads(self.connection.entries[0].entry_to_json()))
			elif self.service == 'ldap-group':
				self.connect()
				self.search()
				self.group_members()
				self.report(self.members)
			else:
				self.error('Invalid service')

if __name__ == '__main__':
    LDAPAnalyzer().run()
