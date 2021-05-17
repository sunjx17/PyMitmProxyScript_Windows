# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import Levenshtein as Lv
import re
from mitmproxy import ctx
twin=10

def getfilters():
    repts=[]
    filt=ET.parse('FilterSettings.xml').getroot()
    fi=filt.findall('OfficialFilter/FilterItem')
    for f in fi:
        f0=f.text
        repts.append(re.compile(f0))
    return repts
def find_rowmax(l,nowmaxid):
    #print('find %d'%(nowmaxid))
    j=nowmaxid
    for k in l[j]['similar']:
        if l[k]['simax']>l[j]['simax'] and not l[k]['remove']:
            nowmaxid=k
    if nowmaxid==j:
        return nowmaxid
    else:
        return find_rowmax(l,nowmaxid)
def jian_rowmax(l,mid):
    if int(l[mid]['simax'])>1:
        if int(l[mid]['simax'])>2:
            l[mid]['content']='(%d)'%(l[mid]['simax'])+l[mid]['content']
            l[mid]['type']=5
        l[mid]['size']=25+min(40,l[mid]['simax']*3)
        l[mid]['weifan']-=min(5,l[mid]['simax']/5)
        
        #print('find %d (%.1f) string(%d) %s '%(mid,l[mid]['time'],l[mid]['simax'],l[mid]['content']))
        
        for k in l[mid]['similar']:
            if not l[k]['remove']:
                
                l[k]['remove']=True
                l[k]['simax']=0
                for kk in l[k]['similar']:
                    if not l[kk]['remove']:
                        l[kk]['simax']-=1
                    #l[kk]['similar']
        
        l[mid]['simax']=0
def parse_sim(l,i,use_jaro,use_win,timewindow,jaro_similarity,win_similarity):

    
        for j in range(i):
            #print('now %d'%(j))
            for k in range(j+1,i):
                
                if l[k]['time']-l[j]['time']>timewindow:
                    break
                try:
                    if use_jaro and use_win:
                        conn=(Lv.jaro(l[j]['content'],l[k]['content'])>jaro_similarity) and (Lv.jaro_winkler(l[j]['content'],l[k]['content'])>win_similarity)
                    elif use_jaro:
                        conn=(Lv.jaro(l[j]['content'],l[k]['content'])>jaro_similarity)
                    elif use_win:
                        conn= (Lv.jaro_winkler(l[j]['content'],l[k]['content'])>win_similarity)
                    else:
                        conn=(Lv.ratio(l[j]['content'],l[k]['content'])>win_similarity*jaro_similarity)
                    '''
                    if use_lv=="jaro":
                        conn=(Lv.jaro(l[j]['content'],l[k]['content'])>similarity)
                    #elif use_lv=="ratio":
                    #    conn=(Lv.ratio(l[j]['content'],l[k]['content'])>similarity)
                    elif use_lv=="jaro_winkler":
                        conn=(Lv.ratio(l[j]['content'],l[k]['content'])>similarity)
                    else:
                        conn=(l[j]['content']==l[k]['content'])
                    '''
                    if conn:
                    #if l[j]['content']==l[k]['content']:
                        #print('checkok %d'%(k))
                        l[j]['simax']+=1
                        l[j]['similar'].append(k)
                        l[k]['simax']+=1
                        l[k]['similar'].append(j)
                except Exception as e:
                    print(e)
                    ctx.log.alert(':'+l[j]['content']+":"+l[k]['content'])
                    ctx.log.alert(':'+l[j]['content']+":"+l[k]['content'])

def clr(l,i):
    for j in range(i):
        l[j]['similar']=[]
        l[j]['simax']=1
        l[j]['remove']=False
        l[i]['']
def xml_dic(root):
    i=0;l=[];maxt=0;
    for c in root.findall('d'):
        p=c.get('p').split(',')
        t=float(p[0])
        if t>maxt:
            maxt=t
        l.append({
            'time':t,
            'type':p[1],
            'size':p[2],
            'color':p[3],
            'timestamp':p[4],
            'pool':p[5],
            'uid_crc32':p[6],
            'row_id':p[7],
            'content':str(c.text),
            'similar':[],
            'simax':1,
            'remove':False,
            'weifan':0
            })
        i+=1
        root.remove(c)
        
    return l,i,maxt
def parse_xml(xmlstr:str):
    global twin
    try:
        root=ET.fromstring(xmlstr)
        l,i,maxt=xml_dic(root)
        use_j=True
        use_w=True
        sim_j=0.8
        sim_w=0.7
        if(len(l)>32000):
            ctx.log.alert('too long xml %d,use lv jaro_winkler,window 8,sim 0.76'%(len(l)))
            #use_lv='jaro_winkler'
            use_j=False
            sim_w=0.7
            twin=8
        elif len(l)>20000:
            ctx.log.alert('long xml %d,use lv jaro jaro_winkler,window 9,sim 0.8 0.75'%(len(l)))
            twin=9
        else:
            sim_j=0.85
            sim_w=0.75
            ctx.log.alert('xml len %d,use lv jaro jaro_winkler,window 10,sim 0.9 0.8'%(len(l)))
        l=sorted(l,key=lambda e:e.__getitem__('time'))
        #l2=[]
        parse_sim(l,i,use_j,use_w,twin,sim_j,sim_w)
        
        for j in range(i):
            for filt in filters:
                l[j]['weifan']+=len(filt.findall(l[j]['content']))
            l[j]['weifan']+=5/(len(l[j]['content'])+1)
            if l[j]['remove'] or l[j]['simax']<=1:
                continue
            else:
                while not (l[j]['remove'] and l[j]['simax']<=1):
                    mid=find_rowmax(l,j)
                    #if l[mid]['simax']>2:
                    #    print('from %d(%d) to %d(%d)'%(j,l[j]['simax'],mid,l[mid]['simax']))
                    jian_rowmax(l,mid)
                    if mid==j:
                        break
       
        l=sorted(l,key=lambda e:e.__getitem__('weifan'))
        for j in range(min(i,32000)):
            if not l[j]['remove']:
                b=ET.Element('d')
                b.text=l[j]['content']
                b.set('p',
                       '%.1f,%s,%s,%s,%s,%s,%s,%s'%
                       (l[j]['time'],
                        l[j]['type'],
                        l[j]['size'],
                        l[j]['color'],
                        l[j]['timestamp'],
                        l[j]['pool'],
                        l[j]['uid_crc32'],
                        l[j]['row_id']))
                root.append(b)
        return 200,ET.tostring(root,encoding='utf-8')
    #.replace('<i>','''<?xml version="1.0"?>
    #<i xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">''')
                # l2.append(l[j])
                
    except Exception as ex:
        print(ex)
        return 404,''
        
            
    
                    
filters=getfilters()    
                    
                    
