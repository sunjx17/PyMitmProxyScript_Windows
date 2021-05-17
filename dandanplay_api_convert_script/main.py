# -*- coding: utf-8 -*-
import json
from mitmproxy import http
from mitmproxy import ctx
import os.path as opath
import urllib.parse as urllibp
from pypinyin import lazy_pinyin as lzpy
import time
import imr
import re
import imp
import pymysql

#import base64
imp.reload(imr)
def x2u(hexsx):
    if type(hexsx) is str:
        return  bytes.fromhex(hexsx).decode('utf-8')
    elif type(hexsx) is bytes:
        return hexsx.decode('utf-8')
    else:
         return None
def s2x(S):
    if S!=None:
        return S.encode().hex()
    else:
        return "未识别".encode().hex()

class SQLdb:
    def __init__(self):
        self.db = pymysql.connect(host="localhost",user="root",password="188108",database="animedb")
        self.open=True
        self.cursor = self.db.cursor()
        self.hasGroup=False
        self.AGroupPrev={}
        self.updateAMaxEpEnable=False
    def updateAMaxEp(self,AGroupPrev):
        if self.updateAMaxEpEnable==True:
            sql="""UPDATE animetitle_to_group SET EpMax={0} where AnimeTitle='{1}'"""
            try:
                for Atitle in AGroupPrev:
                    self.cursor.execute(sql.format(AGroupPrev[Atitle][2],Atitle))
                self.db.commit()
            except:
                ctx.log.alert('execute Mysql failed')
    def getAGroupPrev(self):
        if self.hasGroup==False:
            sql='select * from animetitle_to_group'
            try:
                if self.cursor.execute(sql)>0:
                    ret=self.cursor.fetchall()
                    for i in ret:
                        self.AGroupPrev[i[1]]=[i[0],i[2],i[3]]
                    self.hasGroup=True
            except:
                ctx.log.alert('execute Mysql failed')
        return self.AGroupPrev
    def inserts(self,json_raw):
        sql="""REPLACE INTO uid_path (`Id`, `AnimeId`, `EpisodeId`, `Path`, `Hash`, `AnimeTitle`, `EpisodeTitle`, `FileSize`) VALUES """
        app=''
        i=0
        for rw in json_raw:
            i+=1
            #sql="""SELECT AnimeId from uid_path where Path="{0}";""".format(
            app=app+"""('{0}', {1}, {2}, UNHEX("{3}"), '{4}', UNHEX('{5}'), UNHEX('{6}'),{7}),""".format(
                    rw['Id'],rw['AnimeId'],rw['EpisodeId'],
                    s2x(rw['Path']),rw['Hash'],s2x(rw['AnimeTitle']),
                    s2x(rw['EpisodeTitle']),rw['Size']
                )
            #        rw['Path'].encode().hex()
            #        )
            #ctx.log.alert("sql: "+sql)
            #if self.cursor.execute(sql)<=0:
                
                #ctx.log.alert("sql: "+sql)
        sql=sql+app[:-1]
        try:
            ctx.log.info('EXECUTE Mysql，length {0}'.format(i))
            #self.cursor.execute('TRUNCATE TABLE uid_path;')
            self.cursor.execute(sql)
            self.db.commit()
            ctx.log.info('Commit Mysql')
        except pymysql.Error as e:
            ctx.log.alert('execute Mysql failed')
            print(e.args[0], e.args[1])
            self.db.rollback()
        return sql
    def getPathFromHash(self,hash):
        sql="""SELECT Path FROM uid_path WHERE `Hash`="{0}";""".format(hash)
        try:
            if self.cursor.execute(sql)>0:
            #self.db.commit()
                
                v= self.cursor.fetchall()[0][0]
                if v==None:
                    return None
                return x2u(v)
            else:
                return None
        except:
            #self.db.rollback()
            return None
    def getPathFromId(self,id):
        sql="""SELECT Path FROM uid_path WHERE Id="{0}";""".format(id)
        try:
            if self.cursor.execute(sql)>0:
            #self.db.commit()
                v= self.cursor.fetchall()[0][0]
                if v==None:
                    return None
                return x2u(v)
            else:
                return None
        except:
            #self.db.rollback()
            return None
    def getAETitlePathFromId(self,id):
        sql="""SELECT AnimeTitle,EpisodeTitle,Path FROM uid_path WHERE Id="{0}";""".format(id)
        try:
            if self.cursor.execute(sql)>0:
            #self.db.commit()
                at,et,p,= self.cursor.fetchall()[0]
                if at==None or et==None or p==None:
                    return None,None,None
                return x2u(at),x2u(et),x2u(p)
            else:
                return None,None,None
        except:
            #self.db.rollback()
            return None,None,None
    def findSubType(self,id):
        sql="""SELECT SubType FROM uid_path WHERE Id="{0}";""".format(id)
        try:
            if self.cursor.execute(sql)>0:
            #self.db.commit()
                sub,= self.cursor.fetchall()[0]
                if sub==None:
                    return None
                return x2u(sub)
            else:
                return None
        except:
            #self.db.rollback()
            return None
    def setSubType(self,id,sub):
        sql="""UPDATE uid_path SET SubType="{0}" WHERE Id="{1}";""".format(s2x(sub),id)
        try:
            if self.cursor.execute(sql)>0:
                self.db.commit()
        except:
            ctx.log.alert('SQL update sub failed {0}   {1}'.format(s2x(sub),id))
    def close(self):
        if self.open:
            self.db.close()
            self.open=False
    def __del__(self):
        self.close()
class RespModif:
 
    def response(self,flow: http.HTTPFlow):
        if flow.request.pretty_url == "http://127.0.0.1:60119/api/v1/library":
            start=time.time()
            '''with open('tmp.json','w',encoding='utf-8') as f:
                f.write(flow.response.text)'''
            repl=json.loads(flow.response.text)
            ctx.log.alert('repl json len %d'%(len(repl)))
            repl=sorted(repl,key=lambda e:lzpy((e.__getitem__('AnimeTitle') or '未识别')))
            #sdic={}
            #ddic={}
            Db=SQLdb()
            sql=Db.inserts(repl)
            GroupPrev=Db.getAGroupPrev()
            #with open('sql.txt','w',encoding='utf-8') as f:
            #    f.write(sql)
            c=re.compile('第(\d+)话')
            
            for i in range(0,len(repl)):
                #sdic[repl[i]['Id']]=repl[i]['Path']
                #ddic[repl[i]['Hash']]=repl[i]['Path']
                
                if repl[i]['AnimeTitle']!=None:
                    ATitle=repl[i]['AnimeTitle']
                    if GroupPrev.get(ATitle)!=None:
                        #replace Episode Number
                        ep=c.match(repl[i]['EpisodeTitle'])
                        if ep!=None:
                            eps=int(ep.group(1))
                            if eps>GroupPrev[ATitle][2]:
                                GroupPrev[ATitle][2]=eps
                            
                            if GroupPrev[ATitle][2]>100:
                                
                                repl[i]['EpisodeTitle']=(repl[i]['EpisodeTitle'][:ep.start(1)]+
                                    ('{0:0>3d}'.format(eps))+
                                    repl[i]['EpisodeTitle'][ep.end(1):]
                                )
                                #ctx.log.info(repl[i]['AnimeTitle'])
                            else:
                                repl[i]['EpisodeTitle']=(repl[i]['EpisodeTitle'][:ep.start(1)]+
                                    ('{0:0>2d}'.format(eps))+
                                    repl[i]['EpisodeTitle'][ep.end(1):]
                                )
                                #ctx.log.info(repl[i]['AnimeTitle'])
                        #replace Episode Title, and Path with Group
                        if GroupPrev[ATitle][1]!='':
                            repl[i]['EpisodeTitle']=GroupPrev[ATitle][1]+'-'+repl[i]['EpisodeTitle']
                            ATitle=GroupPrev[ATitle][0]
                    #add extension
                    extid=repl[i]['Name'].rfind('.')
                    if extid>0:
                        ext=repl[i]['Name'][extid:]
                        repl[i]['EpisodeTitle']+=ext
                    #Replace Path
                    repl[i]['Path']=ATitle+'\\'+repl[i]['Name']
                    
                else:
                    repl[i]['AnimeTitle']="未识别"
                    path0=repl[i]['Path'][0:len(repl[i]['Path'])-len(repl[i]['Name'])]
                    if len(path0)>11:
                        path0=path0[11:]
                        repl[i]['Path']=path0.replace('\\','-')+'\\.未识别\\'+repl[i]['Name']
            #self.rep=dict.fromkeys(ids,Path)
            '''with open('pathlist.json','w',encoding='utf-8') as f:
                f.write(json.dumps(sdic,ensure_ascii=False))
            with open('hashs.json','w',encoding='utf-8') as f:
                f.write(json.dumps(ddic,ensure_ascii=False))
            '''
            flow.response.set_text(json.dumps(repl,ensure_ascii=False))
            end=time.time();
            ctx.log.alert("get list,time"+str(end-start))
            Db.updateAMaxEp(GroupPrev)
            Db.close()

        elif flow.request.pretty_url.startswith('http://127.0.0.1:60119/api/v1/comment/'):
            start=time.time()
            Hash0=flow.request.pretty_url[len('http://127.0.0.1:60119/api/v1/comment/'):]
            tmpath='./cache/'
            hasfile=opath.isfile(tmpath+Hash0)
            if not hasfile or (hasfile and opath.getsize(tmpath+Hash0)<300):
                if (hasfile and time.time()-opath.getmtime(tmpath+Hash0)>60*60*24*30):
                    ctx.log.alert('Time Out.'+Hash0)
                    return
                ctx.log.alert('resp no cached xml:'+Hash0)
                fL=re.sub(r'\&\#x\d+;',"",flow.response.content.decode('utf-8'))
                sid,repl=imr.parse_xml(fL)
                '''
                if sid==404:
                    sid=200
                    ctx.log.alert('error: save original')
                    repl=fL
                    pass
                '''
                with open(tmpath+Hash0,'w',encoding='utf-8') as f:
                    if type(repl)==bytes:
                        f.write(repl.decode('utf-8'))
                    elif type(repl)==str:
                        f.write(repl)
                        repl=repl.encode('utf-8')
                '''with open('tmp.xml','w',encoding='utf-8') as f:
                    f.write(fL)
                with open('out.xml','w',encoding='utf-8') as f:
                    f.write(repl)
                '''
                
                flow.response = http.HTTPResponse.make(
                            sid,  # (optional) status code
                            repl,#.replace('</d>','</d>\r\n'),  # (optional) content
                            {'Content-Type': 'application/xml; charset=utf-8','Cache-Control': 'no-cache'}  # (optional) headers
                        )
                
            else:
                ctx.log.info('resp find cached xml:'+Hash0)
            end=time.time();
            ctx.log.info("proc xml,time"+str(end-start))            
        
    def request(self,flow:http.HTTPFlow):
    
        purl=flow.request.pretty_url
        if purl.startswith('http://127.0.0.1:60119/api/v1/subtitle/info/'):
            start=time.time()
            uid=purl[len('http://127.0.0.1:60119/api/v1/subtitle/info/'):]
            ctx.log.info("match .."+uid)
            Db=SQLdb()
            At,Et,pth=Db.getAETitlePathFromId(uid)
            if pth!=None:
            #if opath.isfile('pathlist.json'):
                #with open('tmp.json','r',encoding='utf-8') as f:
                #    repl=json.loads(f.read())
                #with open('pathlist.json','r',encoding='utf-8') as f:
                #    sdic=json.loads(f.read())
                #pth=sdic.get(uid)
                lid=pth.rfind('.')
                if(lid>0):
                    ss=pth[:lid]
                else:
                    ss=pth
                '''
                for i in range(len(repl)):
                    if repl[i]['Id']==uid:
                        pth=repl[i]['Path']
                        lid=pth.rfind('.')
                        if(lid>0):
                            ss=pth[:lid]
                        ctx.log.alert(uid+':'+ss)
                        break
                '''    
                if ss!=None:
                    ctx.log.info(uid+':'+ss)
                    #ok=False
                    cont={'subtitles':[]}
                    ret=404
                    b1=[".",".utf.",'.zh.',
                        ".chs&jap.",".gb."  ,".chs.",".chs.rev.",'.SumiSora.sc.','.sc_EMD.',".sc.",".sc-EVA-FANS.",'.SC&JP.','.chs&jpn.','.KXTP.gb.','.Airota.gb.',
                        ".cht&jap.",".big5.",".cht.",".cht.rev.",'.SumiSora.tc.','.tc_EMD.',".tc.",'.TC&JP.']
                    b2=['ssa','ass','vtt','srt']
                    bhas=''
                    for i in range(len(b1)):
                        for j in range(len(b2)):
                            b=b1[i]+b2[j]
                            file=ss+b
                            if opath.isfile(file):
                                bhas=b
                                #with open(file,'rb') as f:
                                #    cont=f.read()
                                #cont['subtitles'].append({'fileName':file.replace("\\","__SLASH__").replace(':','__MH__'),'fileSize':opath.getsize(file)})
                                #ok=True
                                ret=200
                                ctx.log.info('find sub :'+file)
                                break
                        if bhas!="":
                            
                            Db.setSubType(uid,bhas)
                            
                            ctx.log.info('sql store sub:'+bhas)
                            cont['subtitles'].append({'fileName':At+'.'+Et+'['+bhas+']','fileSize':opath.getsize(ss+bhas)})
                            break
                        
                    flow.response = http.HTTPResponse.make(
                        ret,  # (optional) status code
                        json.dumps(cont,ensure_ascii=False),  # (optional) content
                        {'Content-Type': 'application/json; charset=utf-8'}  # (optional) headers
                    )
                    
                    '''
                    if ok:
                        flow.response = http.HTTPResponse.make(
                            200,  # (optional) status code
                            cont,  # (optional) content
                            {'Content-Type': 'application/ass'}  # (optional) headers
                        )
                    else:
                        flow.response = http.HTTPResponse.make(
                            200,  # (optional) status code
                            cont,  # (optional) content
                            {'Content-Type': 'application/ass'}  # (optional) headers
                        )
                    '''
            end=time.time()
            ctx.log.info('find sub take time '+str(end-start))
        elif purl.startswith('http://127.0.0.1:60119/api/v1/subtitle/file/'):
            start=time.time()

            uid_pathx=purl[len('http://127.0.0.1:60119/api/v1/subtitle/file/'):]
            uid=uid_pathx[:36]
            
            DBOK=False
            Db=SQLdb()
            subType=Db.findSubType(uid)
            if subType!=None and len(subType)>1:
                ctx.log.info('from uid get subType {0}'.format(subType))
                path=Db.getPathFromId(uid)
                if path!=None:
                    lid=path.rfind('.')
                    if(lid>0):
                        ss=path[:lid]
                    else:
                        ss=path
                    file=ss+subType
                    if opath.isfile(file):
                        ctx.log.info('from uid exist file: {0}'.format(file))
                        DBOK=True
                    else:
                        ctx.log.alert('from uid Not exist file: {0}'.format(file))
            if not DBOK:
                last0=purl.rfind('?')
                
                if last0>0:
                    rawP=purl[last0+10:]
                    rawP=urllibp.unquote(rawP)
                    file=''
                    file=rawP.replace('__SLASH__',"\\").replace('__MH__',':')
                    if opath.isfile(file):
                        ctx.log.info('get file from req:'+file)
                        DBOK=True
                    else:
                        ctx.log.alert('get file from req not exist: {0}'.format(file))
            if DBOK:
                with open(file,'rb') as f:
                    cont=f.read()
                    
                    flow.response = http.HTTPResponse.make(
                        200,  # (optional) status code
                        cont,  # (optional) content
                        {'Content-Type': 'application/ass'}  # (optional) headers
                    )
            else:
                flow.response = http.HTTPResponse.make(
                    404,  # (optional) status code
                    b"404 not found",  # (optional) content
                    {'Content-Type': 'text/plain'}  # (optional) headers
                )
                '''
                flow.response = http.HTTPResponse.make(
                    302,  # (optional) status code
                    b"""<html>
                    <head>
                    <title>Moved</title>
                    </head>
                    <body>
                    <h1>Moved</h1>
                    <p>This page has moved to <a href="http://www.example.org/">http://www.example.org/</a>.</p>
                    </body>
                    </html>""",  # (optional) content
                    {"Location":flow.request.pretty_url,'Content-Type': 'video/mp4'}  # (optional) headers
                )'''
            end=time.time()
            ctx.log.info('find sub take time '+str(end-start))
        elif purl.startswith('http://127.0.0.1:60119/api/v1/comment/'):
            Hash0=flow.request.pretty_url[len('http://127.0.0.1:60119/api/v1/comment/'):]
            tmpath='./cache/'
            if opath.isfile(tmpath+Hash0) and opath.getsize(tmpath+Hash0)>10:
                with open(tmpath+Hash0,'r',encoding='utf-8') as f:
                    repl=f.read()
                    sid=200
                    ctx.log.info('req found cahced xml:'+Hash0)
                    flow.response = http.HTTPResponse.make(
                        sid,  # (optional) status code
                        repl.encode('utf-8'),#.replace('</d>','</d>\r\n'),  # (optional) content
                        {'Content-Type': 'application/xml; charset=utf-8'}  # (optional) headers
                    )
            else:
                ctx.log.alert('req no cached xml:'+Hash0)
addons = [
    RespModif()
]
