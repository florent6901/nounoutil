import os,sqlite3,calendar,io,datetime as dt
from flask import Flask,request,jsonify,send_file,g
app=Flask(__name__,static_folder='static',static_url_path='')
DB=os.environ.get('DB','/data/asmat.db'); os.makedirs(os.path.dirname(DB),exist_ok=True)
F=['name','nanny_id','hw','dw','weeks','rate','indem','meal','mode','dsick','maj','net2brut','kmrate','sex']
CF=F[1:13]+['sun','dnm']
c=sqlite3.connect(DB)
c.executescript("""create table if not exists nannies(id integer primary key,name text);
create table if not exists children(id integer primary key,name,nanny_id,hw,dw,weeks,rate,indem,meal,mode,dsick,maj,net2brut);
create table if not exists days(child_id,date,status,hours,meals,primary key(child_id,date));
create table if not exists contracts(id integer primary key,child_id,start,nanny_id,hw,dw,weeks,rate,indem,meal,mode,dsick,maj,net2brut,kmrate);
create table if not exists ndays(nanny_id,date,status,primary key(nanny_id,date));""")
for q in ['alter table children add column kmrate','alter table days add column km','alter table children add column sex','alter table days add column comment','alter table children add column sun','alter table children add column dnm','alter table contracts add column sun','alter table contracts add column dnm']:
    try: c.execute(q)
    except Exception: pass
if not c.execute('select 1 from contracts limit 1').fetchone():
    for r in c.execute('select id,nanny_id,hw,dw,weeks,rate,indem,meal,mode,dsick,maj,net2brut,kmrate from children').fetchall():
        c.execute('insert into contracts(child_id,start,nanny_id,hw,dw,weeks,rate,indem,meal,mode,dsick,maj,net2brut,kmrate) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(r[0],'2000-01-01',*r[1:]))
c.commit(); c.close()
def db():
    if 'db' not in g: g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row
    return g.db
@app.teardown_appcontext
def close(e):
    d=g.pop('db',None); d and d.close()
def rows(sql,*a): return [dict(r) for r in db().execute(sql,a)]
def run(sql,*a): db().execute(sql,a); db().commit()
@app.get('/api/state')
def state(): return jsonify(nannies=rows('select * from nannies'),children=rows('select * from children'),contracts=rows('select * from contracts order by start'))
@app.post('/api/nanny')
def nanny():
    j=request.json
    run('update nannies set name=? where id=?',j['name'],j['id']) if j.get('id') else run('insert into nannies(name) values(?)',j['name'])
    return {}
@app.delete('/api/nanny/<int:i>')
def dnanny(i):
    if rows('select 1 from contracts where nanny_id=?',i): return {'error':'Cette nounou est liée à un contrat : supprimer d\'abord le contrat ou l\'enfant.'}
    run('delete from ndays where nanny_id=?',i); run('delete from nannies where id=?',i); return {}
def sync(i):
    cs=rows('select * from contracts where child_id=? order by start',i); t=dt.date.today().isoformat(); x=([k for k in cs if k['start']<=t] or cs)[-1 if [k for k in cs if k['start']<=t] else 0]
    run('update children set '+','.join(k+'=?' for k in CF)+' where id=?',*[x[k] for k in CF],i)
@app.post('/api/child')
def child():
    j=request.json; i=j.get('id')
    if i: run('update children set name=?,sex=? where id=?',j['name'],j.get('sex'),i)
    else: i=db().execute('insert into children(name,sex) values(?,?)',(j['name'],j.get('sex'))).lastrowid
    v=[j.get(k) for k in CF]; st=j.get('start') or '2000-01-01'
    if j.get('cid'): run('update contracts set '+','.join(k+'=?' for k in CF)+',start=? where id=?',*v,st,j['cid'])
    else: run('insert into contracts(child_id,start,'+','.join(CF)+') values(?,?,'+','.join('?'*len(CF))+')',i,st,*v)
    sync(i); return {'id':i}
@app.delete('/api/child/<int:i>')
def dchild(i): run('delete from days where child_id=?',i); run('delete from contracts where child_id=?',i); run('delete from children where id=?',i); return {}
@app.delete('/api/contract/<int:i>')
def dcontract(i):
    r=rows('select child_id from contracts where id=?',i)
    if r and rows('select count(*) n from contracts where child_id=?',r[0]['child_id'])[0]['n']>1: run('delete from contracts where id=?',i); sync(r[0]['child_id'])
    return {}
@app.post('/api/day')
def day():
    j=request.json; cid=j['child_id']; sk=0
    cs=cts(cid)
    for d in j['dates']:
        ex=(rows('select * from days where child_id=? and date=?',cid,d) or [{}])[0]
        v=lambda k:j[k] if k in j else ex.get(k)
        st=v('status') or ''
        if st and rows('select 1 from ndays where nanny_id=? and date=?',at(cs,d)['nanny_id'],d): sk+=1; continue
        hrs,ml,km,cm=v('hours') or None,v('meals'),v('km') or None,(v('comment') or '').strip() or None
        run('delete from days where child_id=? and date=?',cid,d)
        if st or km or cm: run('insert into days values(?,?,?,?,?,?,?)',cid,d,st,hrs,ml,km,cm)
    return {'skipped':sk}
@app.post('/api/nday')
def nday():
    j=request.json; cs=cts(j['child_id']); rm=0
    for d in j['dates']:
        n=at(cs,d)['nanny_id']; run('delete from ndays where nanny_id=? and date=?',n,d)
        if j['status']:
            run('insert into ndays values(?,?,?)',n,d,j['status'])
            for ch in rows('select id from children'):
                if at(cts(ch['id']),d)['nanny_id']==n: rm+=db().execute("update days set status='',hours=null,meals=null where status!='' and date=? and child_id=?",(d,ch['id'])).rowcount
    db().execute("delete from days where status='' and km is null and comment is null"); db().commit(); return {'removed':rm}
def cts(i): return rows('select * from contracts where child_id=? order by start',i)
def at(cs,d):
    x=[k for k in cs if k['start']<=d]; return x[-1] if x else cs[0]
NUM=['P','A','S','NV','NM','norm','comp','maj','sunh','net','brut','ind','rep','km','kme']
def calc(k,dl,n,d,nm):
    hd=k['hw']/k['dw']; wk={}; P=S=A=meals=km=sunh=0
    for r in d:
        km+=r.get('km') or 0
        if r['status']=='P':
            P+=1; h=r['hours'] or hd; r['eh']=h; sunh+=h if dt.date.fromisoformat(r['date']).weekday()==6 else 0; w=dt.date.fromisoformat(r['date']).isocalendar()[1]; wk[w]=wk.get(w,0)+h; meals+=1 if r['meals'] is None else r['meals']
        elif r['status']=='S': S+=1
        elif r['status']=='A': A+=1
    comp=maj=norm=0; mens=k['mode']=='mensualise'
    for T in wk.values():
        mj=max(T-45,0); maj+=mj
        if mens: comp+=max(min(T,45)-k['hw'],0)
        else: norm+=T-mj
    NM=sum(nm.get(x)=='M' for x in dl); NV=sum(nm.get(x)=='V' for x in dl)
    if mens: norm=max(k['hw']*k['weeks']/12*len(dl)/n-((NM if k.get('dnm') in (None,1) else 0)+(S if k['dsick'] else 0))*hd,0)+comp
    net=norm*k['rate']+maj*k['rate']*(1+k['maj']/100)+sunh*k['rate']*(k.get('sun') or 0)/100
    return dict(P=P,A=A,S=S,NV=NV,NM=NM,norm=norm,comp=comp,maj=maj,net=net,brut=net/k['net2brut'],ind=P*k['indem'],rep=meals*k['meal'],km=km,kme=km*(k['kmrate'] or 0),sunh=sunh)
def recap(c,ym):
    y,m=map(int,ym.split('-')); n=calendar.monthrange(y,m)[1]; cs=cts(c['id']); d=rows('select * from days where child_id=? and date like ?',c['id'],ym+'%'); seg={}; nmall={}; sg=[]; T={q:0 for q in NUM}
    for i in range(1,n+1): x=f'{ym}-{i:02d}'; seg.setdefault(at(cs,x)['id'],[]).append(x)
    for k in cs:
        dl=seg.get(k['id'])
        if not dl: continue
        nm={r['date']:r['status'] for r in rows('select * from ndays where nanny_id=? and date like ?',k['nanny_id'],ym+'%') if r['date'] in dl}; nmall.update(nm)
        o=calc(k,dl,n,[r for r in d if r['date'] in dl],nm)
        for q in NUM: T[q]+=o[q]
        sg.append(dict(**{q:k[q] for q in ['nanny_id','hw','dw','weeks','rate','indem','meal','kmrate','mode','maj','sun']},nanny=(rows('select name from nannies where id=?',k['nanny_id']) or [{'name':'?'}])[0]['name'],frm=dl[0],to=dl[-1],total=round(o['net']+o['ind']+o['rep']+o['kme'],2)))
    R=lambda v:round(v,2)
    L=[('Jours de présence',T['P']),('Absences enfant',T['A']),('Enfant malade',T['S']),('Nounou en vacances',T['NV']),('Nounou malade',T['NM']),('Heures normales',R(T['norm'])),('Heures complémentaires incluses',R(T['comp'])),('Heures majorées',R(T['maj'])),('Heures dimanche majorées',R(T['sunh'])),('Salaire net (€)',R(T['net'])),('Salaire brut estimé (€)',R(T['brut'])),("Indemnités d'entretien (€)",R(T['ind'])),('Repas (€)',R(T['rep'])),('Km parcourus',round(T['km'],1)),('Indemnités km (€)',R(T['kme'])),('TOTAL à verser (€)',R(T['net']+T['ind']+T['rep']+T['kme']))]
    return L,d,sg,nmall
@app.get('/api/month')
def month():
    c=rows('select * from children where id=?',request.args['child'])[0]; L,d,sg,nm=recap(c,request.args['ym'])
    return jsonify(days={r['date']:r for r in d},ndays=nm,lines=L,segs=sg)
def fm(k,v):
    if '(€)' in k: return k.replace(' (€)',''),f"{v:.2f}".replace('.',',')+' €'
    return k,str(v).replace('.',',')
MN=['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre']
SL={'P':'Présent','A':'Absent','S':'Malade'}; NL={'V':'Nounou en vacances','M':'Nounou malade'}
def pdf(c,nn,ym,L,d,nd,b,sg):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle as PS
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer
    H=colors.HexColor; PR=H('#5b6cff'); y,m=map(int,ym.split('-')); W=178*mm
    t=PS('t',fontName='Helvetica-Bold',fontSize=20,leading=24,textColor=colors.white); st=PS('st',fontName='Helvetica',fontSize=11,leading=14,textColor=colors.white)
    sm=PS('sm',fontName='Helvetica',fontSize=8.5,leading=10); hd=c['hw']/c['dw']
    ban=Table([[[Paragraph(c['name'],t),Paragraph(f'Récapitulatif mensuel — {MN[m-1]} {y}',st)]]],colWidths=[W]); ban.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PR),('LEFTPADDING',(0,0),(-1,-1),14),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
    eu=lambda v:f'{v:.2f}'.replace('.',',')+' €'; md='mensualisé' if c['mode']=='mensualise' else 'heures réelles'
    inf=Table([['Nounou',nn,'Taux horaire net',eu(c['rate'])+' / h'],['Contrat',f"{c['hw']:g} h/sem sur {c['dw']:g} j · {c['weeks']:g} sem/an","Indemnité d'entretien",eu(c['indem'])+' / jour'],['Mode',md,'Repas · Km',f"{eu(c['meal'])} · {eu(c['kmrate'] or 0)}/km"],['Majorations',f"Dimanche {c.get('sun') or 0:g} %",'Au-delà de 45 h',f"{c['maj']:g} %"]],colWidths=[22*mm,64*mm,40*mm,52*mm])
    inf.setStyle(TableStyle([('FONT',(0,0),(-1,-1),'Helvetica',9),('FONT',(0,0),(0,-1),'Helvetica-Bold',9),('FONT',(2,0),(2,-1),'Helvetica-Bold',9),('TEXTCOLOR',(0,0),(0,-1),PR),('TEXTCOLOR',(2,0),(2,-1),PR),('BACKGROUND',(0,0),(-1,-1),H('#f3f5fb')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    sgt=None
    if len(sg)>1:
        sgt=Table([['Période','Nounou','Taux net','Entretien/j','H/sem','Total']]+[[f"{x['frm'][8:]}/{m:02d} → {x['to'][8:]}/{m:02d}",x['nanny'],eu(x['rate']),eu(x['indem']),f"{x['hw']:g}",eu(x['total'])] for x in sg],colWidths=[40*mm,36*mm,24*mm,28*mm,18*mm,32*mm])
        sgt.setStyle(TableStyle([('FONT',(0,0),(-1,-1),'Helvetica',8.5),('FONT',(0,0),(-1,0),'Helvetica-Bold',8.5),('BACKGROUND',(0,0),(-1,0),H('#e9ecff')),('TEXTCOLOR',(0,0),(-1,0),PR),('LINEBELOW',(0,0),(-1,-1),.3,H('#d5d9ea')),('ALIGN',(2,0),(-1,-1),'RIGHT')]))
    rows_=[];sty=[('FONT',(0,0),(-1,-1),'Helvetica',10),('ALIGN',(1,0),(1,-1),'RIGHT'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.4,H('#e8ebf5'))]
    for h,idx in [('PRÉSENCES',range(0,5)),('HEURES & SALAIRE (Pajemploi)',range(5,11)),('INDEMNITÉS',range(11,15))]:
        sty+=[('SPAN',(0,len(rows_)),(1,len(rows_))),('BACKGROUND',(0,len(rows_)),(1,len(rows_)),H('#e9ecff')),('FONT',(0,len(rows_)),(0,len(rows_)),'Helvetica-Bold',8.5),('TEXTCOLOR',(0,len(rows_)),(0,len(rows_)),PR)]
        rows_.append([h,'']); rows_+=[list(fm(*L[i])) for i in idx]
    rows_.append(list(fm(*L[15]))); k=len(rows_)-1
    sty+=[('BACKGROUND',(0,k),(1,k),PR),('TEXTCOLOR',(0,k),(1,k),colors.white),('FONT',(0,k),(1,k),'Helvetica-Bold',12)]
    rec=Table(rows_,colWidths=[W-50*mm,50*mm]); rec.setStyle(TableStyle(sty))
    nm={r['date']:r['status'] for r in nd}; dm={r['date']:r for r in d}
    dates=sorted({x for x,r in dm.items() if r['status'] or r.get('km') or r.get('comment')}|set(nm))
    data=[['Date','Enfant','Nounou','Heures','Repas','Km','Commentaire']];cs=[]
    for i,x in enumerate(dates,1):
        r=dm.get(x,{}); dd=__import__('datetime').date.fromisoformat(x); p=r.get('status')=='P'
        data.append([f"{['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][dd.weekday()]} {dd.day:02d}/{dd.month:02d}",SL.get(r.get('status'),''),NL.get(nm.get(x),''),f"{(r.get('eh') or r.get('hours') or hd):g}" if p else '',(1 if r.get('meals') is None else r['meals']) if p else '',f"{r['km']:g}" if r.get('km') else '',Paragraph((r.get('comment') or '').replace('<','&lt;'),sm)])
        col=H({'V':'#dff3fd','M':'#f8e1fb'}[nm[x]]) if x in nm else H({'P':'#dcf7ec','A':'#fff1d6','S':'#ffe0e3'}.get(r.get('status'),'#ffffff'))
        cs.append(('BACKGROUND',(0,i),(-1,i),col))
    det=Table(data,colWidths=[24*mm,20*mm,34*mm,15*mm,14*mm,12*mm,59*mm],repeatRows=1)
    det.setStyle(TableStyle([('FONT',(0,0),(-1,-1),'Helvetica',8.5),('FONT',(0,0),(-1,0),'Helvetica-Bold',8.5),('BACKGROUND',(0,0),(-1,0),PR),('TEXTCOLOR',(0,0),(-1,0),colors.white),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,0),(-1,-1),.3,H('#d5d9ea')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]+cs))
    h2=PS('h2',fontName='Helvetica-Bold',fontSize=12,textColor=PR,spaceBefore=14,spaceAfter=6)
    def ft(cv,_):
        cv.setFont('Helvetica',8); cv.setFillColor(H('#7c84a3')); cv.drawString(16*mm,8*mm,'Généré par Nounoutil (Suivi Assmat) — '+__import__('datetime').date.today().strftime('%d/%m/%Y')); cv.drawRightString(194*mm,8*mm,f'Page {cv.getPageNumber()}')
    SimpleDocTemplate(b,pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=14*mm,bottomMargin=16*mm).build([ban,Spacer(1,8),inf]+([Paragraph('Contrats sur la période',h2),sgt] if sgt else [])+[Paragraph('Récapitulatif',h2),rec,Paragraph('Détail des jours',h2),det if dates else Paragraph('Aucun événement ce mois-ci.',sm)],onFirstPage=ft,onLaterPages=ft)
def build(c,ym,fmt):
    L,d,sg,nm=recap(c,ym); nd=[{'date':k,'status':v} for k,v in nm.items()]; b=io.BytesIO()
    nn=' → '.join(dict.fromkeys(x['nanny'] for x in sg)); c={**c,**sg[-1]}
    if fmt=='xlsx':
        from openpyxl import Workbook
        from openpyxl.styles import PatternFill,Font,Alignment,Border,Side
        y,m=map(int,ym.split('-')); fl=lambda h:PatternFill('solid',fgColor=h); bd=Border(bottom=Side(style='thin',color='D5D9EA')); EUR='#,##0.00 "€"'
        def ban(w,rng,txt,h=34):
            w.merge_cells(rng); x=w[rng.split(':')[0]]; x.value=txt; x.font=Font(size=15,bold=True,color='FFFFFF'); x.fill=fl('5B6CFF'); x.alignment=Alignment(vertical='center',indent=1); w.row_dimensions[1].height=h
        wb=Workbook(); ws=wb.active; ws.title='Récap'; ws.sheet_view.showGridLines=False; ws.column_dimensions['A'].width=40; ws.column_dimensions['B'].width=36
        ban(ws,'A1:B1',f'Récapitulatif mensuel — {MN[m-1]} {y}')
        info=[('Enfant',c['name']),('Assistante maternelle',nn),('Taux horaire net',c['rate']),("Indemnité d'entretien / jour",c['indem']),('Contrat',f"{c['hw']:g} h/sem sur {c['dw']:g} j · {c['weeks']:g} sem/an"),('Mode','Mensualisé' if c['mode']=='mensualise' else 'Heures réelles'),('Majorations',f"Dimanche {c.get('sun') or 0:g} % · > 45 h {c['maj']:g} %")]+([('Contrats',f'{len(sg)} sur ce mois (voir PDF)')] if len(sg)>1 else [])
        for i,(k,v) in enumerate(info,2):
            ws.cell(i,1,k).font=Font(bold=True,color='5B6CFF'); x=ws.cell(i,2,v); x.alignment=Alignment(horizontal='right')
            if isinstance(v,float) or isinstance(v,int): x.number_format=EUR
            for q in (1,2): ws.cell(i,q).fill=fl('F3F5FB')
        r=len(info)+3
        for h,idx in [('PRÉSENCES',range(0,5)),('HEURES & SALAIRE (Pajemploi)',range(5,11)),('INDEMNITÉS',range(11,15))]:
            ws.merge_cells(start_row=r,start_column=1,end_row=r,end_column=2); ws.cell(r,1,h).font=Font(bold=True,size=9,color='5B6CFF'); ws.cell(r,1).fill=fl('E9ECFF'); r+=1
            for i in idx:
                k,v=L[i]; ws.cell(r,1,k.replace(' (€)','')); x=ws.cell(r,2,v); x.alignment=Alignment(horizontal='right')
                if '(€)' in k: x.number_format=EUR
                for q in (1,2): ws.cell(r,q).border=bd
                r+=1
        ws.cell(r,1,'TOTAL à verser'); ws.cell(r,2,L[15][1]).number_format=EUR
        for q in (1,2): x=ws.cell(r,q); x.font=Font(bold=True,size=13,color='FFFFFF'); x.fill=fl('5B6CFF'); x.alignment=Alignment(horizontal='left' if q==1 else 'right',vertical='center')
        ws.row_dimensions[r].height=26
        w2=wb.create_sheet('Jours'); w2.sheet_view.showGridLines=False; ban(w2,'A1:G1',f"{c['name']} · {nn} — {MN[m-1]} {y}")
        for j,(hn,wd) in enumerate(zip(['Date','Enfant','Nounou','Heures','Repas','Km','Commentaire'],[14,12,22,9,9,9,50]),1):
            x=w2.cell(3,j,hn); x.font=Font(bold=True,color='FFFFFF'); x.fill=fl('5B6CFF'); x.alignment=Alignment(horizontal='center'); w2.column_dimensions[chr(64+j)].width=wd
        nm={r['date']:r['status'] for r in nd}; dm={r['date']:r for r in d}; row=4
        for x in sorted({k for k,r in dm.items() if r['status'] or r.get('km') or r.get('comment')}|set(nm)):
            r_=dm.get(x,{}); dd=dt.date.fromisoformat(x); col={'V':'DFF3FD','M':'F8E1FB'}[nm[x]] if x in nm else {'P':'DCF7EC','A':'FFF1D6','S':'FFE0E3'}.get(r_.get('status'),'FFFFFF')
            for j,v in enumerate([f"{['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'][dd.weekday()]} {dd.day:02d}/{dd.month:02d}",SL.get(r_.get('status'),''),NL.get(nm.get(x),''),r_.get('hours'),r_.get('meals'),r_.get('km'),r_.get('comment')],1):
                z=w2.cell(row,j,v); z.fill=fl(col); z.border=bd; z.alignment=Alignment(wrap_text=j==7,vertical='center',horizontal='left' if j in(1,2,3,7) else 'center')
            row+=1
        w2.freeze_panes='A4'; ws.page_setup.fitToWidth=1; wb.save(b); mt='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else: pdf(c,nn,ym,L,d,nd,b,sg); mt='application/pdf'
    b.seek(0); return b,mt
@app.get('/api/export/<fmt>')
def export(fmt):
    c=rows('select * from children where id=?',request.args['child'])[0]; ym=request.args['ym']; b,mt=build(c,ym,fmt)
    return send_file(b,mimetype=mt,as_attachment=True,download_name=f'recap-{c["name"]}-{ym}.{fmt}')
@app.get('/api/active')
def active():
    o={}
    for r in rows("select child_id,substr(date,1,7) m from days where status!='' or km is not null or comment is not null group by child_id,m"): o.setdefault(r['child_id'],[]).append(r['m'])
    return jsonify(o)
@app.get('/api/bulk')
def bulk():
    import zipfile
    ids=request.args['children'].split(','); ms=sorted(request.args['months'].split(',')); fs=request.args['fmt'].split(','); z=io.BytesIO()
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as zf:
        for i in ids:
            c=rows('select * from children where id=?',i)[0]; n=c['name'].replace('/','-')
            for ym in ms:
                for f in fs: zf.writestr(f'{n}/{ym}-{n}.{f}',build(c,ym,f)[0].getvalue())
    z.seek(0); return send_file(z,mimetype='application/zip',as_attachment=True,download_name='exports-asmat.zip')
@app.get('/')
def idx(): return app.send_static_file('index.html')
