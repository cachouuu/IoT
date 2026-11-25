from pathlib import Path
import re,html,json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,Table,TableStyle,PageBreak,NextPageTemplate,Preformatted,Flowable
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(TTFont('JH',r'C:\Windows\Fonts\msjh.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('JHB',r'C:\Windows\Fonts\msjhbd.ttc',subfontIndex=0))
pdfmetrics.registerFontFamily('JH',normal='JH',bold='JHB',italic='JH',boldItalic='JHB')
NAVY=colors.HexColor('#14364B'); TEAL=colors.HexColor('#087E8B'); GRAY=colors.HexColor('#53616A'); PALE=colors.HexColor('#EDF5F7')
styles={
 'body':ParagraphStyle('body',fontName='JH',fontSize=10.2,leading=16.1,spaceAfter=8,wordWrap='CJK',splitLongWords=True,textColor=colors.HexColor('#202A31')),
 'h1':ParagraphStyle('h1',fontName='JHB',fontSize=19,leading=27,spaceAfter=16,textColor=NAVY,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='JHB',fontSize=12.2,leading=19,spaceBefore=9,spaceAfter=6,textColor=NAVY,keepWithNext=True),
 'cell':ParagraphStyle('cell',fontName='JH',fontSize=9,leading=13.4,wordWrap='CJK',splitLongWords=True),
 'head':ParagraphStyle('head',fontName='JHB',fontSize=9,leading=13.4,wordWrap='CJK',textColor=colors.white),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=8.2,leading=12,spaceAfter=10,leftIndent=8),
 'small':ParagraphStyle('small',fontName='JH',fontSize=8.8,leading=13,wordWrap='CJK',spaceAfter=6)
}
def rich(s):
    s=html.escape(s.replace('\u2212','-'))
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`([^`]+)`',r'\1',s)
    return s
def para(s,style='body'):return Paragraph(rich(s),styles[style])
def footer(c,doc):
    w,h=c._pagesize
    c.saveState();c.setFont('JH',8);c.setFillColor(GRAY)
    c.drawString(42,24,'DIC3  |  交通配時助手  |  2026-11-13')
    c.drawRightString(w-42,24,f'{doc.page:02d}')
    c.restoreState()
class Architecture(Flowable):
    def __init__(self):Flowable.__init__(self);self.width=500;self.height=286
    def draw(self):
        c=self.canv
        def box(x,y,w,h,title,sub,fill=PALE):
            c.setFillColor(fill);c.setStrokeColor(colors.HexColor('#BED1DA'));c.roundRect(x,y,w,h,5,fill=1,stroke=1)
            c.setFillColor(NAVY);c.setFont('JHB',10);c.drawCentredString(x+w/2,y+h-14,title)
            c.setFont('JH',8);c.drawCentredString(x+w/2,y+8,sub)
        def line(x1,y1,x2,y2):
            c.setStrokeColor(TEAL);c.setLineWidth(1);c.line(x1,y1,x2,y2)
            import math
            a=math.atan2(y2-y1,x2-x1)
            for d in (-.5,.5):c.line(x2,y2,x2-5*math.cos(a+d),y2-5*math.sin(a+d))
        x=122;w=235;h=32
        nodes=[('1 任務入口','資料批次／模式／政策'),('2 資料資格檢查','來源、時間、單位與完整性'),('3 分析引擎','FIFO 與過去 30 秒四特徵'),('4 決策與回退','既有決策樹／規則來源'),('6 依據與任務紀錄','真實特徵、方案及理由'),('7 ARM／FPGA 執行','提交方案／週期邊界採用'),('8 回讀與結果','active_plan／cycle_count')]
        ys=[252-i*40 for i in range(7)]
        for i,(t,s) in enumerate(nodes):
            box(x,ys[i],w,h,t,s)
            if i:line(x+w/2,ys[i-1],x+w/2,ys[i]+h)
        box(370,132,128,32,'5 領域限制','合法方案／相位／期限',colors.HexColor('#FFF2D9'))
        line(370,148,357,148);c.setStrokeColor(TEAL);c.line(434,132,434,68);line(434,68,357,68)
        box(0,212,107,32,'資料不足','拒絕控制並說明',colors.HexColor('#FAECEB'));line(122,228,107,228)
        c.setStrokeColor(TEAL);c.line(122,28,113,28);c.line(113,28,113,188);line(113,188,122,188)

def table(rows,width,land=False):
    n=len(rows[0]);title=' '.join(rows[0]);fractions=None
    if n==8: fractions=[.12,.06,.10,.14,.12,.15,.14,.17]
    elif n==5 and '作業' not in title:fractions=[.28,.15,.19,.15,.23]
    elif n==4:fractions=[.17,.30,.32,.21]
    elif n==3:fractions=[.19,.49,.32]
    elif n==6:fractions=[.18,.15,.15,.13,.17,.22]
    if fractions is None:fractions=[1/n]*n
    fractions=[f/sum(fractions) for f in fractions]
    data=[[para(cell,'head' if i==0 else 'cell') for cell in row] for i,row in enumerate(rows)]
    if n==8:
        for j, cell in enumerate(rows[0]):
            if 'Domain' in cell: data[0][j]=Paragraph('Domain<br/>Knowledge',styles['head'])
    t=Table(data,colWidths=[f*width for f in fractions],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.45,colors.HexColor('#CBD6DC')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F4F7F9')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    return t

def parse_chunk(chunk,land=False):
    width=(landscape(A4)[0] if land else A4[0])-84
    lines=chunk.strip().splitlines();story=[];i=0
    while i<len(lines):
        l=lines[i].strip()
        if not l:i+=1;continue
        if l.startswith('```'):
            block=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
            story.append(Preformatted('\n'.join(block),styles['code']));i+=1;continue
        if l.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                r=[s.strip() for s in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+',s) for s in r):rows.append(r)
                i+=1
            story+=[table(rows,width,land),Spacer(1,10)];continue
        if l=='[[architecture]]':story+=[Architecture(),Spacer(1,9)];i+=1;continue
        if l.startswith('# '):story.append(para(l[2:],'h1'));i+=1;continue
        if l.startswith('## '):story.append(para(l[3:],'h2'));i+=1;continue
        p=[l];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```','[[')):
            p.append(lines[i].strip());i+=1
        style='small' if p[0].startswith(('[A','[D','[O','[P','[H')) else 'body'
        story.append(para(' '.join(p),style))
    return story

def main_report():
    doc=BaseDocTemplate(str(ROOT/'Traffic_Assistant_DIC3_Report.pdf'),pagesize=A4,leftMargin=42,rightMargin=42,topMargin=43,bottomMargin=44,title='交通配時助手提案與規格重整',author='第13組交通配時助手')
    templates=[]
    for name,size in [('portrait',A4),('landscape',landscape(A4))]:
        w,h=size;templates.append(PageTemplate(id=name,frames=[Frame(42,44,w-84,h-87,id=name,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],pagesize=size,onPage=footer))
    doc.addPageTemplates(templates)
    raw=(ROOT/'DIC3_Report.md').read_text(encoding='utf-8')
    parts=re.split(r'<!-- (page|landscape) -->',raw)
    story=parse_chunk(parts[0]);
    for i in range(1,len(parts),2):
        mode='landscape' if parts[i]=='landscape' else 'portrait'
        story += [NextPageTemplate(mode),PageBreak()]+parse_chunk(parts[i+1],mode=='landscape')
    doc.build(story)

def overview():
    out=ROOT/'Traffic_Assistant_DIC3_Overview.pdf';c=canvas.Canvas(str(out),pagesize=landscape(A4));W,H=landscape(A4)
    c.setTitle('交通配時助手 A4 專題總覽');c.setAuthor('第13組交通配時助手')
    c.setFillColor(NAVY);c.rect(0,H-65,W,65,fill=1,stroke=0)
    c.setFont('JHB',22);c.setFillColor(colors.white);c.drawString(28,H-33,'交通配時助手  |  DIC3 規格總覽')
    c.setFont('JH',10);c.drawString(29,H-52,'單路口兩軸 × 三種配時 × ARM 決策 × FPGA 執行回讀')
    gap=12;col=(W-56-2*gap)/3
    cards=[
    ('01  A 注意與價值','需求不均時，固定綠燈分配可能不合適。以開發板展示資料如何轉成配時決定，並核對實際生效。'),
    ('02  B 三個挑戰','資料可取得未必可控制；推薦未必已執行；平均改善可能掩蓋退步案例與方向代價。'),
    ('03  C 解法','結構化任務＋來源資格檢查＋小型決策樹＋規則回退＋統一證據報告。'),
    ('04  D 方法','四特徵：兩向估計佇列與過去 30 秒到車。三方案：12/12、16/8、8/16 秒。完整週期邊界採用。'),
    ('05  E 評估','相同保存輸入比較固定與模型＋回退。主要指標是排隊車秒，並列放行數、等待、剩車與回退。'),
    ('06  F 預期產出','可解釋且可追溯的課程原型、規格與驗收情境。既有 18 組合計改善 18.28%，但 5 組退步。')]
    def card(x,y,w,h,title,text,fill=PALE):
        c.setFillColor(fill);c.setStrokeColor(colors.HexColor('#D0DDE3'));c.roundRect(x,y,w,h,6,fill=1,stroke=1)
        c.setFillColor(NAVY);c.setFont('JHB',12);c.drawString(x+12,y+h-22,title)
        st=ParagraphStyle('card',fontName='JH',fontSize=10,leading=16,wordWrap='CJK',textColor=colors.HexColor('#263E4A'))
        p=Paragraph(html.escape(text),st);pw,ph=p.wrap(w-24,h-43);p.drawOn(c,x+12,y+h-37-ph)
    for i,(t,txt) in enumerate(cards):card(28+(i%3)*(col+gap),H-65-12-(i//3+1)*113-(i//3)*gap,col,113,t,txt)
    y=55;h=174
    card(28,y,col,h,'07  五個核心','C1 資料可追溯\nC2 需求狀態建模\nC3 有限且可解釋決策\nC4 決策與執行分工\nC5 同條件評估'.replace('\n','；'),colors.HexColor('#F2F5F8'))
    card(28+col+gap,y,col,h,'08  三個取捨','T1 規則直接決策或樹模型近似：保留樹與規則回退。\nT2 反應速度或時序一致：週期邊界更新。\nT3 合計效率或方向代價：保留反例與剩車。'.replace('\n',' '),colors.HexColor('#FFF5E3'))
    card(28+2*(col+gap),y,col,h,'09  十個細節','D01 範圍　D02 任務欄位\nD03 資料資格　D04 介面容量\nD05 因果特徵　D06 模型域\nD07 合法方案　D08 相位時序\nD09 生效確認　D10 績效邊界'.replace('\n','；'),colors.HexColor('#F2F5F8'))
    c.setFillColor(GRAY);c.setFont('JH',8.5);c.drawString(28,35,'狀態：提案／OpenSpec 文件已完成；通用任務層仍待整合。現有結果為合成 FIFO 評估，不是道路實測效益。')
    c.drawString(28,20,'來源：原提案 2026-11-03、DESIGN.md、既有實驗紀錄；完整文獻與驗證見主報告及 evidence/。  2026-11-13')
    c.save()
main_report();overview()
print('Created report and A4 overview')
