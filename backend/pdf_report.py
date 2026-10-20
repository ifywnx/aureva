import io
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,KeepTogether

FONT=Path(__file__).resolve().parents[1]/'assets/fonts/NotoSans.ttf'
def render_report(snapshot):
    pdfmetrics.registerFont(TTFont('Aureva',str(FONT)))
    styles=getSampleStyleSheet()
    for name in ('Normal','Title','Heading1','Heading2'):styles[name].fontName='Aureva'
    styles['Normal'].fontSize=9
    styles['Normal'].leading=15
    styles.add(ParagraphStyle('Small',fontName='Aureva',fontSize=7,leading=11,textColor=colors.HexColor('#64776d')))
    styles['Title'].textColor=colors.HexColor('#22674f')
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=(210*mm,297*mm),rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=20*mm,title='AUREVA - Báo cáo minh bạch',author='AUREVA')
    p=lambda s,style='Normal':Paragraph(escape(str(s)).replace('\n','<br/>'),styles[style])
    money=lambda n:f'{n:,}'.replace(',','.')+' VND'
    c=snapshot['campaign']
    story=[p('AUREVA','Title'),p('Trao gửi yêu thương, rõ từng đóng góp.'),Spacer(1,8*mm),p('BÁO CÁO MINH BẠCH CHIẾN DỊCH','Heading2'),p(c['title'],'Heading1'),p(c['description']),Spacer(1,4*mm),p('Địa bàn: '+c['location']),p('Phụ trách: '+c['manager_name']),p('Thời điểm chốt số liệu (UTC): '+snapshot['created']),p('Mã báo cáo: '+snapshot['report_id'],'Small'),Spacer(1,6*mm)]
    table=Table([[p('Đóng góp đã đối soát'),p('Khoản chi đã duyệt'),p('Số dư')],[p(money(c['raised'])),p(money(c['spent'])),p(money(c['raised']-c['spent']))]],colWidths=[58*mm]*3)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#eef4ee')),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),10)]))
    story.extend([table,Spacer(1,5*mm),p('Chi đã duyệt là quyết định phân bổ kinh phí, không phải xác nhận đã chuyển tiền. Các khoản đóng góp chờ đối soát không được tính trong báo cáo.','Small')])
    for title,rows,expense in [('ĐÓNG GÓP ĐÃ ĐỐI SOÁT',snapshot['donations'],False),('QUYẾT ĐỊNH KHOẢN CHI',snapshot['expenses'],True)]:
        story.extend([Spacer(1,6*mm),p(title,'Heading2')])
        if not rows:story.append(p('Chưa có giao dịch.'));continue
        cells=[[p('Nội dung'),p('Số tiền'),p('Trạng thái / thời điểm')]]
        for r in rows:
            content=r.get('purpose','Đóng góp cứu trợ')
            if r.get('reason'):content+='\nLý do: '+r['reason']
            status={'approved':'Đã duyệt','rejected':'Từ chối'}.get(r.get('status'),'Đã đối soát')
            cells.append([p(content),p(money(r['amount'])),p(status+'\n'+r['created'][:10])])
        table=Table(cells,colWidths=[95*mm,40*mm,39*mm],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8f0e9')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#dce6dc')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
        story.append(table)
    story.extend([Spacer(1,7*mm),p('KIỂM TRA TÍNH TOÀN VẸN','Heading2'),p('Tra cứu mã báo cáo trên AUREVA để xem dữ liệu chốt, SHA-256 của PDF, mã băm bản ghi và trạng thái Blockchain hiện tại. Chỉ khi có giao dịch được xác nhận trên Sepolia mới có bằng chứng ghi nhận trên chuỗi. Bản PDF này không tự tuyên bố đã được xác nhận Blockchain.'),p('Không công khai danh tính người đóng góp, mã chuyển khoản hoặc file chứng từ gốc.','Small')])
    def footer(canvas,doc):
        canvas.setFont('Aureva',8);canvas.setFillColor(colors.HexColor('#7c8d80'));canvas.drawString(18*mm,12*mm,'AUREVA | Báo cáo từ dữ liệu đã chốt');canvas.drawRightString(192*mm,12*mm,f'Trang {doc.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()
