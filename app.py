import os
import json
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from supabase_py import create_client
from dotenv import load_dotenv
from flask_mail import Mail, Message
import seaborn as sns
import io
import base64
from fpdf import FPDF
from PIL import Image
import numpy as np
from datetime import datetime
from flask import Flask, Response, request, send_file, make_response, jsonify
from fpdf.enums import XPos, YPos

from modules.pie_waiting import generate_pie_waiting
from modules.tables import generate_top_5, generate_worst_5
from modules.bar_feedback import generate_image
from modules.pie_feedback import generate_pie_feedback
from modules.pie_followup import generate_pie_followup
from modules.pie_gender import generate_pie_gender

app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'rajasthanhackathon4@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

plt.switch_backend('Agg')

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return 'Rajasthan Police Station Feedback Data API'


@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    table_name = 'visits'
    response = supabase.table(table_name).select().execute()
    rows = response['data']
    df = pd.DataFrame(rows)
    df['Feeling'] = df['Feel'].apply(lambda x: 'positive' if x > 0 else 'negative')
    grouped_data = df.groupby(['policeStation', 'Feeling']).size().unstack(fill_value=0).reset_index()
    grouped_data.columns = ['policeStation', 'Negative Feel', 'Positive Feel']
    
    try:
        send_email_param = request.args.get('send_email', '').lower()
        
        if send_email_param == 'true':
            pdf_bytes = plot_grouped_bar_chart_as_pdf(grouped_data)
            mailme(pdf_bytes)
        
        result = {'status': 'OK', 'data': grouped_data.to_dict(orient='records')}
    except Exception as e:
        result = {'status': 'FAILED', 'error': str(e)}
    
    response_json = json.dumps(result, ensure_ascii=False)
    return Response(response_json, content_type='application/json; charset=utf-8')


@app.route('/fetch_stats', methods=['GET'])
def fetch_stats():
    table_name = 'psStats'
    response = supabase.table(table_name).select().execute()
    rows = response['data']
    df = pd.DataFrame(rows)
    
    if request.args.get('city'):
        city_param = request.args.get('city').upper()
        ps_df = df.loc[df['City'] == city_param]
        
        feedbacks = ps_df['Negative_Feedback'].sum() + ps_df['Positive_Feedback'].sum()
        top5 = generate_top_5(ps_df)
        worst5 = generate_worst_5(ps_df)
        pie1 = generate_pie_feedback(ps_df)
        pie2 = generate_pie_followup(ps_df)
        pie3 = generate_pie_gender(ps_df)
        pie4 = generate_pie_waiting(ps_df)
        img_buffer = generate_image(df)
        pdf_buffer = create_pdf(img_buffer, top5, worst5, feedbacks, pie1, pie2, pie3, pie4)
        send_email_param = request.args.get('send_email', '').lower()
        if send_email_param == 'true':
            mailme(pdf_buffer.getvalue(),city_param)
            return 'Mail Sent'
        else:
            return send_file(pdf_buffer, download_name='output.pdf', as_attachment=True)
        
    else:
        feedbacks = df['Negative_Feedback'].sum() + df['Positive_Feedback'].sum()
        top5 = generate_top_5(df)
        worst5 = generate_worst_5(df)
        pie1 = generate_pie_feedback(df)
        pie2 = generate_pie_followup(df)
        pie3 = generate_pie_gender(df)
        pie4 = generate_pie_waiting(ps_df)
        img_buffer = generate_image(df)
        pdf_buffer = create_pdf(img_buffer, top5, worst5, feedbacks, pie1, pie2, pie3,pie4)
        send_email_param = request.args.get('send_email', '').lower()
        if send_email_param == 'true':
            mailme(pdf_buffer.getvalue())
            return 'Mail Sent'
        else:
            return send_file(pdf_buffer, download_name='output.pdf', as_attachment=True)


def create_pdf(buffer,top5,worst5,feedbacks,pie1,pie2,pie3,pie4):
    pdf = FPDF()
    
    pdf.add_page()
    available_width = pdf.w - 2 * pdf.l_margin
    image_size = 10  # Adjust the size as needed
    pdf.set_font("Helvetica", "B", 16)
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, text="January Month Rajasthan Police Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)
    pdf.set_line_width(1.05)
    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(20)  # Move down a bit
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="Overview", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

    pdf.ln(5)  # Move down a bit
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, text=f"Number of Feedbacks this Month: {feedbacks}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    
    pie1 = Image.open(pie1)
    pie2 = Image.open(pie2)
    pie3 = Image.open(pie3)
    pie4 = Image.open(pie4)

    pdf.ln(5)  # Move down a bit
    pdf.image(pie1, x=pdf.l_margin, y=pdf.get_y(), w=available_width/2)
    pdf.image(pie2, x=pdf.l_margin + available_width/2, y=pdf.get_y(), w=available_width/2)
    pdf.ln(90)
    pdf.image(pie4, x=pdf.l_margin, y=pdf.get_y(), w=available_width/2)
    pdf.image(pie3, x=pdf.l_margin + available_width/2, y=pdf.get_y(), w=available_width/2)

    pdf.add_page()
    image_size = 10  # Adjust the size as needed

    pdf.set_font("Helvetica", "B", 16)

    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)

    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, text="January Month Rajasthan Police Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')


    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)


    pdf.set_line_width(1.05)


    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    pdf.ln(20)  # Move down a bit
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="Top 5 Performing Police Stations", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')


    img = Image.open(top5)
    img_width, img_height = img.size


    image_aspect_ratio = img_width / img_height
    new_width = available_width
    new_height = new_width / image_aspect_ratio

    pdf.image(top5, x=pdf.l_margin, y=pdf.get_y(), w=new_width, h=new_height)


    pdf.ln(new_height+5)  # Move down a bit
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="Worst 5 Performing Police Stations", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')


    img = Image.open(worst5)
    img_width, img_height = img.size


    image_aspect_ratio = img_width / img_height
    new_width = available_width
    new_height = new_width / image_aspect_ratio

    pdf.image(worst5, x=pdf.l_margin, y=pdf.get_y(), w=new_width, h=new_height)    
    
    pdf.add_page()
    image_size = 10  # Adjust the size as needed

    pdf.set_font("Helvetica", "B", 16)

    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)

    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, text="January Month Rajasthan Police Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')


    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)


    pdf.set_line_width(1.05)


    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    pdf.ln(10)  # Move down a bit
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="City Wise Feedbacks", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    img = Image.open(buffer)
    img_width, img_height = img.size

    # Calculate new width and height to maintain aspect ratio
    aspect_ratio = img_width / img_height
    new_height = pdf.h - pdf.get_y() - 10
    new_width = aspect_ratio * new_height

    pdf.image(buffer, x=pdf.l_margin, y=pdf.get_y()+5, w=new_width, h=new_height)
    
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)

    return pdf_buffer


def mailme(pdf_bytes, city=None):
    all_emails = ['rajasthanhackathon4@gmail.com']
    current_month = datetime.now().strftime("%B")
    
    with app.app_context():
        with mail.connect() as conn:
            for email in all_emails:
                message = 'A small gist of how was the performance of Rajasthan Police Stations'
                
                # Modify the subject based on the current month
                subject = f"{current_month} Rajasthan Police Station Report"
                
                # Append city name before "Rajasthan" if city parameter is given
                if city:
                    subject = f"{city} {subject}"
                    message = f"A small gist of how was the performance of {city} Rajasthan Police Stations"
                
                msg = Message(recipients=[email], sender='Harsh Varshney', \
                              body=message, subject=subject)
                msg.attach("Report.pdf", 'application/pdf', pdf_bytes)
                
                conn.send(msg)
if __name__ == '__main__':
    app.run(debug=True)