#!/usr/bin/env python

import os
import uuid
import json
import tornado.ioloop
import tornado.web
from tornado import websocket
from Logs import Log

import pdb

#############################################
#  Main class to handle all group_name of users.
##############################################
class GroupHandler(object):
    """Store data about connections, rooms, which users are in which rooms, etc."""
    def __init__(self):
        self.user_info = {}    #  user_info['user_id'] = {'wsconn': wsconn, 'group_name':group_name, 'user_name':user_name}
        self.group_info = {}   #  group_info['group_name'] = {'group_id':group_id, 'user_list':[id1,id2,...] } 

    def addNewGroup(self, group_name, user_name):
        """ Adding a new Group
            Adding a new user
            Adding the user in that Group
            Return group-id
        """
        #1. Adding User..
        #what is the uniue user_id.. like ravi1, ravi2 ...
        c = 1
        user_id = user_name
        nir = [ ui['user_name'] for ui in self.user_info.values()  ]
        while True:
            if user_id in nir:
                user_id = user_name + str(c)
            else:
                break
            c += 1

        self.user_info[user_id] = {'wsconn': None, 'group_name': group_name, 'user_name': user_id}  #we still don't know the WS connection for this user
        
        #2. Adding Group if doent exist..
        group_id = uuid.uuid4().hex  # generate a new group_name id
        if not group_name in self.group_info:  # it's a new group_name
            self.group_info[group_name] = {'group_id':group_id, 'user_list':[user_id] } 
        else:
           self.group_info[group_name]['user_list'].append(user_id)
        return {'user_id':user_id,'group_id':group_id}

    def updateUserConn(self, user_id, conn):
        """ Update the connection for that user
            update the connection info in roommates
        """
        #pdb.set_trace()
        self.user_info[user_id]['wsconn'] = conn
        user_name = self.user_info[user_id]['user_name']
        
        #Send Join Message.... 
        group_name = self.user_info[user_id]['group_name']
        grp_conns = self.getAllUserConnInGroup(group_name)
        self.sendGroupMessage(grp_conns,'join','system', user_name+'join the room..')
        self.sendGroupMessage(grp_conns,'nick_list','system', user_name+'join the room..')
    
    def removeUser(self, user_id):
        """ 
            update the connection info in roommates
        """
        group_name = self.user_info[user_id]['group_name']
        user_name = self.user_info[user_id]['user_name']
        
        #Remove from user_info        
        del self.user_info[user_id]   
        print 'Removing user',user_name
        #Remove from Group Info
        self.group_info[group_name]['user_list'].remove(user_id)
        if( self.group_info[group_name]['user_list'] == []):
           del self.group_info[group_name]
           print 'Removing Group',group_name
        
        # Send The group Leave Notification..
        grp_conns = self.getAllUserConnInGroup(group_name)
        self.sendGroupMessage(grp_conns,'leave','system', user_name+'left the room..')
        
    def getGroupNameForUser(self,user_id):
      return  self.user_info[user_id]['group_name']
      
    def getAllUserConnInGroup(self, group_name):
        """Return a list with the nicknames of the users currently connected to the specified group_name."""
        if group_name not in self.group_info:
          return []
        conns = []  # nicks in group_name
        for uid in self.group_info[group_name]['user_list']:
           conns.append(self.user_info[uid]['wsconn'])
        return conns;   
    def getAllUserConnInGroupExceptSender(self, group_name,user_id):
        """Return a list with the nicknames of the users currently connected to the specified group_name."""
        if group_name not in self.group_info:
            return []
        conns = []  # nicks in group_name
        for uid in self.group_info[group_name]['user_list']:
           if uid != user_id:
               conns.append(self.user_info[uid]['wsconn'])
        return conns;    

    @staticmethod
    def sendGroupMessage(conns,msg_type,sender, msg):
        """Send a message of type 'nick_list' (contains a list of nicknames) to all the specified connections."""
        msg = {"msgtype": msg_type, "sender":sender, "payload": msg}
        pmessage = json.dumps(msg)
        for c in conns:
            c.write_message(pmessage)

############################################
# This class is to Crete/Join for a user
############################################
class MainHandler(tornado.web.RequestHandler):
    def initialize(self, group_handler):
        """Store a reference to the "external" GroupHandler instance"""
        self.__gh = group_handler
    def get(self):
        """Render chat.html if required arguments are present, render main.html otherwise."""
        try:
            group_name = self.get_argument("group_name")
            user_name = self.get_argument("user_name")
            res = self.__gh.addNewGroup(group_name, user_name)
            self.render("templates/chat.html", user_id=res['user_id'])
        except Exception,e:
            print e
            Log(e)
            self.render("templates/main.html")

class UserWSCouser_idection(websocket.WebSocketHandler):
    def initialize(self, group_handler):
        """Store a reference to the "external" GroupHandler instance"""
        self.__gh = group_handler
    def check_origin(self, origin):
        return True
    def open(self, user_id):
        self.__userID = user_id
        self.__gh.updateUserConn(user_id, self)
        print "WebSocket opened. UserID = %s" % self.__userID
    def on_message(self, message):
        msg = json.loads(message)
        msg['username'] = self.__gh.user_info[self.__userID]['user_name']
        pmessage = json.dumps(msg)
        group_name = self.__gh.getGroupNameForUser(self.__userID)
        rconns = self.__gh.getAllUserConnInGroup(group_name)
        for conn in rconns:
            conn.write_message(pmessage)

    def on_close(self):
        print "WebSocket closed"
        self.__gh.removeUser(self.__userID)

if __name__ == "__main__":
    rh = GroupHandler()
    app = tornado.web.Application([
        (r"/", MainHandler, {'group_handler': rh}),
        (r"/ws/(.*)", UserWSCouser_idection, {'group_handler': rh})],
        static_path=os.path.join(os.path.dirname(__file__), "static")
    )
    app.listen(8888)
    print 'Simple Chat Server started.'
    print 'listening on 8888 ...'
    tornado.ioloop.IOLoop.instance().start()

