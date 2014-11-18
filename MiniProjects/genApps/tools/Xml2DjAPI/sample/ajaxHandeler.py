from common import D_LOG
import json
from bson import json_util
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

#Helper function
def AutoHttpResponse(code=200,res=None):
  if res and isinstance(res, dict):
    return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json')
  if code == 400:  
    res = {'res':None,'status':'error','msg':'400(Bad Request): '+str(res)} if res else {'res':None,'status':'error','msg':'400(Bad Request): required /invalid Paranmeter passed.'}
  if code == 501:  
    res = {'res':None,'status':'error','msg':'501(Not Implemented): '+str(res)} if res else {'res':None,'status':'error','msg':'501(Not Implemented)'}
  return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json') 

#We support "[1,2,3]" or 'aa,bb,cc' or 'aa bb cc' to [1,2,3] Split Over , space or eval 
def str2List(s):
  s = s.strip()
  try:
    if '[' in s:
      return eval(s)
    if ',' in s:
      return [ _i.strip() for _i in s.split(',') if _i]
    else:
      return [ _i for _i in s.split(' ') if _i ]
  except:
    D_LOG()
    print 'Error: eval Error: We support "[1,2,3]" or "aa,bb,cc" or "aa bb cc" to [1,2,3] Split Over , space or eval '
    return []
  
#Helper Function To Perse Advance Serach parmas
#Input : <a:b:c> =>(a,b,c) >
def parseTriple(s):
  if not s: # for null check..
    return s
  res = [None,None,None]
  s = s.split(':')
  if len(s) >= 3:
    s[0] = '|' if s[0].lower() == 'or' else '&'   
    res = s[:3]
  elif len(s) == 2:
    res = ['|'] + s
  elif len(s) ==1:
    res = ['|','exact']+s
  if len(res[0]) == 0 : res[0] ="|"
  if len(res[1]) == 0 : res[1] ="exact"
  # rule for in and not in
  if res[1] in ['in','notin']:
    res[2] =  str2List(res[2])  
  return res
  


from .api import AuthorManager
@csrf_exempt
def ajax_Author(request,id=None):
  res=None
  
  #If the request is coming for get ..
  if request.method == 'GET':
    page=request.GET.get('page',None)
    limit=request.GET.get('limit',None)
    name=request.GET.get('name',None);reg=request.GET.get('reg',None);history=request.GET.get('history',None);tag1=request.GET.get('tag1',None);tag2=request.GET.get('tag2',None);
    #data Must be Normalized to required DataType..
    try:
      name = str(name) if( name) else name ;reg = int(reg) if( reg) else reg ;history = dict(history) if( history) else history ;tag1 = str2List(tag1) if( tag1) else tag1 ;tag2 = str2List(tag2) if( tag2) else tag2 ;
    except:
      D_LOG()
      return AutoHttpResponse(400,'Type mismatch!you might be trying to enter Wrong datatype')
    # if Id is null, get the perticular Author or it's a search request
    if id is not None: 
      res= AuthorManager.getAuthor(id)
    else:
      # General Search request 
      id=request.GET.get('id',None) # We also support search based on ID.
      res= AuthorManager.searchAuthor(name=name,reg=reg,history=history,tag1=tag1,tag2=tag2,id=id,page=page,limit=limit,  )
    
  #This is the implementation for POST request.
  elif request.method == 'POST':
    name=request.POST.get('name',None);reg=request.POST.get('reg',None);history=request.POST.get('history',None);tag1=request.POST.get('tag1',None);tag2=request.POST.get('tag2',None);    
    #data Must be Normalized to required DataType..
    try:
      name = str(name) if( name) else name ;reg = int(reg) if( reg) else reg ;history = dict(history) if( history) else history ;tag1 = str2List(tag1) if( tag1) else tag1 ;tag2 = str2List(tag2) if( tag2) else tag2 ;
    except:
      D_LOG()
      return AutoHttpResponse(400,'Type mismatch!you might be trying to enter Wrong datatype')
    # Update request if id is not null. 
    if id is not None: 
      res=AuthorManager.updateAuthor(id=id,name=name,reg=reg,history=history,tag1=tag1,tag2=tag2,)
    else:
      # This is new entry request...
      res=AuthorManager.createAuthor(name=name,reg=reg,history=history,tag1=tag1,tag2=tag2,)
    
  # This is a Delete Request..
  elif request.method ==  'DELETE' and id is not None:
    res =AuthorManager.deleteAuthor(id)
  #Return the result after converting into json 
  return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json')


@csrf_exempt
def ajax_Author_list(request,id=None,):
  res=None
  # This is basically a search by a tag or list items with given arguments
  if request.method == 'GET':
    return AutoHttpResponse(501)
  # This is basically a append to a list with given arguments
  elif request.method == 'POST':
    action=request.POST.get('action',None)
    if action not in ['APPEND', 'REMOVE', 'SEARCH'] : return AutoHttpResponse(400,'id missing ! your post data must have action = APPEND or REMOVE or SEARCH ?')     
    if not id and action != 'SEARCH' : return AutoHttpResponse(400,'id missing ! is your urls looks like http://192.168.56.101:7777/api/Author/1/list/ ?')   

    try:
      tag1 = eval(request.POST.get('tag1','[]'));tag2 = eval(request.POST.get('tag2','[]'));
      if action == 'APPEND':
        res = AuthorManager.appendListAuthor(id,tag1=tag1,tag2=tag2,)
      elif action == 'REMOVE':
        res = AuthorManager.removeListAuthor(id,tag1=tag1,tag2=tag2,)
      elif action == 'SEARCH':
        res = AuthorManager.searchListAuthor(tag1=tag1,tag2=tag2,)
    except:
      D_LOG()
      return AutoHttpResponse(400,'list item is not speared properly! Is your list field looks like: tags = [1,2,3] or tag1=%5B1%2C2%2C3%5D ?')

  #Return the result after converting into json
  return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json')


<<<<<<< HEAD
@csrf_exempt
def ajax_Author_asearch(request): # We support POST only .
  res=None
=======
#   query_str_builder() Will build query_str from triples
def query_str_builder(key,v):
  if v[1] in ['tagin', 'tagnotin']:
    v2 = str2List(v[2])
    if v2[0][0] != '-':
      _m = ' '+v[0]+'( Q('+key+'__contains = "'+v2[0]+'") ' # BUG ? if we have two tag c and ccc, then ?
    else:
      _m = ' '+v[0]+'( ~Q('+key+'__contains = "'+v2[0][1:]+'") '
    for L in v2[1:]:
      if L[0] != '-':
        _m += ' & Q('+key+'__contains = "'+L+'") '
      else:
        _m += ' & ~Q('+key+'__contains = "'+L[1:]+'") '
    return _m +' ) '
    
  if v[1] in ['in', 'notin']:
    return v[0]+' Q('+key+'__'+v[1]+' = '+str(v[2])+') ' # this is a list in case of in/notin
  else:
    return v[0]+' Q('+key+'__'+v[1]+' = "'+str(v[2])+'") ' # else the v[2] will be String

@csrf_exempt
def ajax_Author_asearch(request): # We support POST only .
  res=None
  #import pdb
  #pdb.set_trace()
>>>>>>> 13e7a4c0e378aa9e5e08d4179d7c9a2d28bd24a3
  # This is basically a search by a tag or list items with given arguments
  if request.method == 'GET':
    return AutoHttpResponse(501)
  # This is basically a append to a list with given arguments
  elif request.method == 'POST':
<<<<<<< HEAD
    id=request.POST.get('id',None)
    import pdb
    pdb.set_trace()
    
    pass
    
    if action not in ['APPEND', 'REMOVE', 'SEARCH'] : return AutoHttpResponse(400,'id missing ! your post data must have action = APPEND or REMOVE or SEARCH ?')     
    if not id and action != 'SEARCH' : return AutoHttpResponse(400,'id missing ! is your urls looks like http://192.168.56.101:7777/api/Author/1/list/ ?')   

    try:
      tag1 = eval(request.POST.get('tag1','[]'));tag2 = eval(request.POST.get('tag2','[]'));
      if action == 'APPEND':
        res = AuthorManager.appendListAuthor(id,tag1=tag1,tag2=tag2,)
      elif action == 'REMOVE':
        res = AuthorManager.removeListAuthor(id,tag1=tag1,tag2=tag2,)
      elif action == 'SEARCH':
        res = AuthorManager.searchListAuthor(tag1=tag1,tag2=tag2,)
    except:
      return AutoHttpResponse(400,'list item is not speared properly! Is your list field looks like: tags = [1,2,3] or tag1=%5B1%2C2%2C3%5D ?')

  #Return the result after converting into json
  return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json')
=======
    id=request.POST.get('id',None)    
    try: 
      #name = parseTriple(request.POST.get('name',None));reg = parseTriple(request.POST.get('reg',None));history = parseTriple(request.POST.get('history',None));tag1 = parseTriple(request.POST.get('tag1',None));tag2 = parseTriple(request.POST.get('tag2',None));
      non_field_params = ['orderBy','include','exclude']
      orderBy = request.POST.get('orderBy',None);
      if orderBy: orderBy = orderBy.split(',')
      include = request.POST.get('include',None);
      if include: include = include.split(',')
      exclude = request.POST.get('exclude',None);
      if exclude: exclude = exclude.split(',')
      
      #Define Query Strings.
      queryDict = dict(request.POST)
      for _x in non_field_params:
        if queryDict.has_key(_x):
          del queryDict[_x]
      #Now we should only have Database field.
      Qstr= ''
      for key, value in queryDict.iteritems():         
        if isinstance(value,str):
          v = parseTriple(value)
          if v: Qstr += query_str_builder(key,v)
        else:
          for v in value:
            v = parseTriple(v)
            if v: Qstr += query_str_builder(key,v)
      Qstr = Qstr[2:]         
      
    except:
      D_LOG()
      return AutoHttpResponse(400,'Wrong Pentameter format.') 	   
    
    try:
       res = AuthorManager.advSearchAuthor(id=id,query_str=Qstr,orderBy=orderBy,include=include,exclude=exclude)
    except:
      D_LOG()
      return AutoHttpResponse(400,'list item is not speared properly! Is your list field looks like: tags = [1,2,3] or tag1=%5B1%2C2%2C3%5D ?')
  return AutoHttpResponse(res=res)
>>>>>>> 13e7a4c0e378aa9e5e08d4179d7c9a2d28bd24a3


from .api import PublicationManager
@csrf_exempt
def ajax_Publication(request,id=None):
  res=None
  
  #If the request is coming for get ..
  if request.method == 'GET':
    page=request.GET.get('page',None)
    limit=request.GET.get('limit',None)
    name=request.GET.get('name',None);accid=request.GET.get('accid',None);
    #data Must be Normalized to required DataType..
    try:
      name = str(name) if( name) else name ;accid = int(accid) if( accid) else accid ;
    except:
      D_LOG()
      return AutoHttpResponse(400,'Type mismatch!you might be trying to enter Wrong datatype')
    # if Id is null, get the perticular Publication or it's a search request
    if id is not None: 
      res= PublicationManager.getPublication(id)
    else:
      # General Search request 
      id=request.GET.get('id',None) # We also support search based on ID.
      res= PublicationManager.searchPublication(name=name,accid=accid,id=id,page=page,limit=limit,  )
    
  #This is the implementation for POST request.
  elif request.method == 'POST':
    name=request.POST.get('name',None);accid=request.POST.get('accid',None);    
    #data Must be Normalized to required DataType..
    try:
      name = str(name) if( name) else name ;accid = int(accid) if( accid) else accid ;
    except:
      D_LOG()
      return AutoHttpResponse(400,'Type mismatch!you might be trying to enter Wrong datatype')
    # Update request if id is not null. 
    if id is not None: 
      res=PublicationManager.updatePublication(id=id,name=name,accid=accid,)
    else:
      # This is new entry request...
      res=PublicationManager.createPublication(name=name,accid=accid,)
    
  # This is a Delete Request..
  elif request.method ==  'DELETE' and id is not None:
    res =PublicationManager.deletePublication(id)
  #Return the result after converting into json 
  return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json')


from .api import BookManager
@csrf_exempt
def ajax_Book(request,id=None):
  res=None
  
  #If the request is coming for get ..
  if request.method == 'GET':
    page=request.GET.get('page',None)
    limit=request.GET.get('limit',None)
    name=request.GET.get('name',None);author=request.GET.get('author',None);
    #data Must be Normalized to required DataType..
    try:
      name = str(name) if( name) else name ;author = int(author) if( author) else author ;
    except:
      D_LOG()
      return AutoHttpResponse(400,'Type mismatch!you might be trying to enter Wrong datatype')
    # if Id is null, get the perticular Book or it's a search request
    if id is not None: 
      res= BookManager.getBook(id)
    else:
      # General Search request 
      id=request.GET.get('id',None) # We also support search based on ID.
      res= BookManager.searchBook(name=name,author=author,id=id,page=page,limit=limit,  )
    
  #This is the implementation for POST request.
  elif request.method == 'POST':
    name=request.POST.get('name',None);author=request.POST.get('author',None);    
    #data Must be Normalized to required DataType..
    try:
      name = str(name) if( name) else name ;author = int(author) if( author) else author ;
    except:
      D_LOG()
      return AutoHttpResponse(400,'Type mismatch!you might be trying to enter Wrong datatype')
    # Update request if id is not null. 
    if id is not None: 
      res=BookManager.updateBook(id=id,name=name,author=author,)
    else:
      # This is new entry request...
      res=BookManager.createBook(name=name,author=author,)
    
  # This is a Delete Request..
  elif request.method ==  'DELETE' and id is not None:
    res =BookManager.deleteBook(id)
  #Return the result after converting into json 
  return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json')


@csrf_exempt
def ajax_Book_Author(request,id=None):
  res=None
  #If the request is coming for get to all author
  if request.method == 'GET':
      res= BookManager.getAuthor(id=id)

  #This is the implementation for POST request to add or delete author
  elif request.method == 'POST':
    action=request.POST.get('action',None)
    try:
      author_list=eval(request.POST.get('author_list',None))
    except:
      D_LOG()
      return AutoHttpResponse(400,'bad input for author_list')
    # Update request if id is not null.
    if action == 'ADD':
      res=BookManager.addAuthor(id=id,author_list = author_list)
    else:
      # do a delete action
      res=BookManager.removeAuthor(id=id,author_list = author_list)

  #Return the result after converting into json
  return HttpResponse(json.dumps(res,default=json_util.default),content_type = 'application/json')

