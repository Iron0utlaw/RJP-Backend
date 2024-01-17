import os
from datetime import datetime
from io import BytesIO
from flask import Flask, request, send_file
from flask_mail import Mail, Message
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from supabase_py import create_client
from fpdf import FPDF
from PIL import Image
from fpdf.enums import XPos, YPos
from modules.pie_waiting import generate_pie_waiting
from modules.tables import generate_top_5, generate_worst_5
from modules.bar_feedback import generate_image
from modules.pie_feedback import generate_pie_feedback
from modules.pie_followup import generate_pie_followup
from modules.pie_gender import generate_pie_gender
from modules.pie_behaviour import generate_pie_behaviour
from modules.pie_guidance import generate_pie_guidance
from modules.pie_help import generate_pie_help
from modules.pie_infra import generate_pie_infra
from modules.pie_rating import generate_pie_rating
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "https://feedback-system-police-private.vercel.app"]}})


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
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

@app.route('/fetch_stats', methods=['GET'])
@limiter.limit("1 per second",exempt_when=lambda: not request.args.get('send_email'))
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
        pie_feedback = generate_pie_feedback(ps_df)
        pie_followup = generate_pie_followup(ps_df)
        pie_gender = generate_pie_gender(ps_df)
        pie_waiting = generate_pie_waiting(ps_df)
        pie_behaviour = generate_pie_behaviour(ps_df)
        pie_guidance = generate_pie_guidance(ps_df)
        pie_help = generate_pie_help(ps_df)
        pie_infra = generate_pie_infra(ps_df)
        pie_rating = generate_pie_rating(ps_df)
        img_buffer = generate_image(df)
        pdf_buffer = create_pdf(img_buffer, top5, worst5, feedbacks, pie_feedback, pie_followup, pie_gender, pie_waiting, pie_behaviour, pie_rating,pie_guidance,pie_help,pie_infra)
        send_email_param = request.args.get('send_email', '').lower()
        if send_email_param == 'true':
            mailme(pdf_buffer.getvalue(), city_param)
            return 'Mail Sent'
        else:
            return send_file(pdf_buffer, download_name='output.pdf', as_attachment=True)
    elif request.args.get('ps'):
        ps_param = request.args.get('ps').upper()
        ps_df = df.loc[df['policeStation'] == ps_param]
        feedbacks = ps_df['Negative_Feedback'].sum() + ps_df['Positive_Feedback'].sum()
        city = ''.join(char for char in ps_param if not (char.isdigit() or char.isspace()))
        city_df = df.loc[df['City'] == city]
        top5 = generate_top_5(city_df)
        worst5 = generate_worst_5(city_df)
        pie_feedback = generate_pie_feedback(ps_df)
        pie_followup = generate_pie_followup(ps_df)
        pie_gender = generate_pie_gender(ps_df)
        pie_waiting = generate_pie_waiting(ps_df)
        pie_behaviour = generate_pie_behaviour(ps_df)
        pie_guidance = generate_pie_guidance(ps_df)
        pie_help = generate_pie_help(ps_df)
        pie_infra = generate_pie_infra(ps_df)
        pie_rating = generate_pie_rating(ps_df)
        img_buffer = generate_image(df)
        pdf_buffer = create_pdf(img_buffer, top5, worst5, feedbacks, pie_feedback, pie_followup, pie_gender, pie_waiting, pie_behaviour, pie_rating,pie_guidance,pie_help,pie_infra)
        send_email_param = request.args.get('send_email', '').lower()
        if send_email_param == 'true':
            mailme(pdf_buffer.getvalue(), ps_param)
            return 'Mail Sent'
        else:
            return send_file(pdf_buffer, download_name='output.pdf', as_attachment=True)
    else:
        feedbacks = df['Negative_Feedback'].sum() + df['Positive_Feedback'].sum()
        top5 = generate_top_5(df)
        worst5 = generate_worst_5(df)
        pie_feedback = generate_pie_feedback(df)
        pie_followup = generate_pie_followup(df)
        pie_gender = generate_pie_gender(df)
        pie_waiting = generate_pie_waiting(df)
        pie_behaviour = generate_pie_behaviour(df)
        pie_guidance = generate_pie_guidance(df)
        pie_help = generate_pie_help(df)
        pie_infra = generate_pie_infra(df)
        pie_rating = generate_pie_rating(df)
        img_buffer = generate_image(df)
        pdf_buffer = create_pdf(img_buffer, top5, worst5, feedbacks, pie_feedback, pie_followup, pie_gender, pie_waiting, pie_behaviour, pie_rating,pie_guidance,pie_help,pie_infra)
        send_email_param = request.args.get('send_email', '').lower()
        if send_email_param == 'true':
            mailme(pdf_buffer.getvalue())
            return 'Mail Sent'
        else:
            return send_file(pdf_buffer, download_name='output.pdf', as_attachment=True)

def create_pdf(buffer, top5, worst5, feedbacks, pie_feedback, pie_followup, pie_gender, pie_waiting,pie_behaviour,pie_rating,pie_guidance,pie_help,pie_infra):
    pdf = FPDF()
    
    pdf.add_page()
    available_width = pdf.w - 2 * pdf.l_margin
    image_size = 10
    pdf.set_font("Helvetica", "B", 16)
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size + 2)
    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2
    pdf.cell(text_x)
    pdf.cell(text_width, 10, text="January Month Rajasthan Police Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size - 5, y=pdf.t_margin - 5, w=image_size + 10)
    pdf.set_line_width(1.05)
    pdf.ln(5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="Overview", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, text=f"Number of Feedbacks this Month: {feedbacks}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

    pie_feedback = Image.open(pie_feedback)
    pie_followup = Image.open(pie_followup)
    pie_gender = Image.open(pie_gender)
    pie_waiting = Image.open(pie_waiting)
    pie_help = Image.open(pie_help)
    pie_guidance = Image.open(pie_guidance)
    pie_rating = Image.open(pie_rating)
    pie_behaviour = Image.open(pie_behaviour)
    pie_infra = Image.open(pie_infra)

    pdf.ln(5)
    pdf.image(pie_feedback, x=pdf.l_margin, y=pdf.get_y(), w=available_width / 2)
    pdf.image(pie_rating, x=pdf.l_margin + available_width / 2, y=pdf.get_y(), w=available_width / 2)
    pdf.ln(90)
    pdf.image(pie_followup, x=pdf.l_margin, y=pdf.get_y(), w=available_width / 2)
    pdf.image(pie_gender, x=pdf.l_margin + available_width / 2, y=pdf.get_y(), w=available_width / 2)

    pdf.add_page()
    image_size = 10
    pdf.set_font("Helvetica", "B", 16)
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size + 2)
    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2
    pdf.cell(text_x)
    pdf.cell(text_width, 10, text="January Month Rajasthan Police Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size - 5, y=pdf.t_margin - 5, w=image_size + 10)
    pdf.set_line_width(1.05)
    pdf.ln(5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(5)

    image_width = 80
    image_height = 40
    total_width = 2 * image_width

    start_x = (pdf.w - total_width) / 2

    for row in range(3):
        for col in range(2):
            x_position = start_x + col * image_width
            y_position = pdf.get_y() + row * image_height

            if row == 0 and col == 0:
                current_pie = pie_help
            elif row == 0 and col == 1:
                current_pie = pie_behaviour
            elif row == 1 and col == 0:
                current_pie = pie_guidance
            elif row == 1 and col == 1:
                current_pie = pie_waiting
            elif row == 2 and col == 0:
                current_pie = pie_infra

            pdf.image(current_pie, x=x_position, y=y_position, w=image_width)

        pdf.ln(image_height)

    pdf.ln(5)

    pdf.add_page()
    image_size = 10
    pdf.set_font("Helvetica", "B", 16)
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size + 2)
    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2
    pdf.cell(text_x)
    pdf.cell(text_width, 10, text="January Month Rajasthan Police Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size - 5, y=pdf.t_margin - 5, w=image_size + 10)
    pdf.set_line_width(1.05)
    pdf.ln(5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="Top 5 Performing Police Stations", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    img = Image.open(top5)
    img_width, img_height = img.size
    image_aspect_ratio = img_width / img_height
    new_width = available_width
    new_height = new_width / image_aspect_ratio
    pdf.image(top5, x=pdf.l_margin, y=pdf.get_y(), w=new_width, h=new_height)
    pdf.ln(new_height + 5)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="Worst 5 Performing Police Stations", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    img = Image.open(worst5)
    img_width, img_height = img.size
    image_aspect_ratio = img_width / img_height
    new_width = available_width
    new_height = new_width / image_aspect_ratio
    pdf.image(worst5, x=pdf.l_margin, y=pdf.get_y(), w=new_width, h=new_height)

    pdf.add_page()
    image_size = 10
    pdf.set_font("Helvetica", "B", 16)
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size + 2)
    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2
    pdf.cell(text_x)
    pdf.cell(text_width, 10, text="January Month Rajasthan Police Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size - 5, y=pdf.t_margin - 5, w=image_size + 10)
    pdf.set_line_width(1.05)
    pdf.ln(5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(available_width, 10, text="City Wise Feedbacks", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    img = Image.open(buffer)
    img_width, img_height = img.size
    aspect_ratio = img_width / img_height
    new_height = pdf.h - pdf.get_y() - 10
    new_width = aspect_ratio * new_height
    pdf.image(buffer, x=pdf.l_margin, y=pdf.get_y() + 5, w=new_width, h=new_height)

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
                
                subject = f"{current_month} Rajasthan Police Station Report"
                
                if city:
                    subject = f"{city} {subject}"
                    message = f"A small gist of how was the performance of {city} Rajasthan Police Stations"
                
                msg = Message(recipients=[email], sender='Harsh Varshney', \
                              body=message, subject=subject)
                msg.attach("Report.pdf", 'application/pdf', pdf_bytes)
                
                conn.send(msg)
if __name__ == '__main__':
    app.run(debug=True)