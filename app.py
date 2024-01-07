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
from flask import Flask, Response, request, send_file, make_response




app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'rajasthanhackathon4@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv('PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

plt.switch_backend('Agg')

load_dotenv()  # Load variables from the .env file

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
        pie1 = generate_pie_1(ps_df)
        pie2 = generate_pie_2(ps_df)
        pie3 = generate_pie_3(ps_df)
        img_buffer = generate_image(df)
        pdf_buffer = create_pdf_with_header(img_buffer, top5, worst5, feedbacks, pie1, pie2, pie3)
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
        pie1 = generate_pie_1(df)
        pie2 = generate_pie_2(df)
        pie3 = generate_pie_3(df)
        img_buffer = generate_image(df)
        pdf_buffer = create_pdf_with_header(img_buffer, top5, worst5, feedbacks, pie1, pie2, pie3)
        send_email_param = request.args.get('send_email', '').lower()
        if send_email_param == 'true':
            mailme(pdf_buffer.getvalue())
            return 'Mail Sent'
        else:
            return send_file(pdf_buffer, download_name='output.pdf', as_attachment=True)



def render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')
    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in mpl_table._cells.items():
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    return ax.get_figure(), ax



def generate_pie_1(df):
    sum_column1 = df['Negative_Feedback'].sum()
    sum_column2 = df['Positive_Feedback'].sum()

    sum_values = [sum_column1, sum_column2]

    labels = ['Negative', 'Positive']

    plt.figure(figsize=(6, 6))
    sns.set_palette("pastel")
    plt.pie(x=sum_values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Feedback Distribution')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer


def generate_pie_2(df):
    sum_column1 = df['Follow_No_Response'].sum()
    sum_column2 = df['Follow_Resolved'].sum()
    sum_column3 = df['Follow_Resolving'].sum()

    sum_values = [sum_column1, sum_column2, sum_column3]

    labels = ['No Response', 'Resolved', 'Resolving']

    plt.figure(figsize=(6, 6))
    sns.set_palette("pastel")
    plt.pie(x=sum_values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Resolution Distribution')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer

def generate_pie_3(df):
    sum_column1 = df['Gender_Male'].sum()
    sum_column2 = df['Gender_Female'].sum()
    sum_column3 = df['Gender_Others'].sum()

    sum_values = [sum_column1, sum_column2, sum_column3]

    labels = ['Male', 'Female', 'Others']

    plt.figure(figsize=(6, 6))
    sns.set_palette("pastel")
    plt.pie(x=sum_values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Gender Distribution')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer

def generate_top_5(df):
    dropped = df.drop(columns=['id','Follow_No_Response', 'Follow_Resolved', 'Follow_Resolving', 'Gender_Female', 'Gender_Male', 'Gender_Others'])
    fig,ax = render_mpl_table(dropped.sort_values('ps_Rating').tail(), header_columns=0, col_width=3.0)
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer


def generate_worst_5(df):
    dropped = df.drop(columns=['id','Follow_No_Response', 'Follow_Resolved', 'Follow_Resolving', 'Gender_Female', 'Gender_Male', 'Gender_Others'])
    fig,ax = render_mpl_table(dropped.sort_values('ps_Rating').head(), header_columns=0, col_width=3.0)
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer


def generate_image(df):
    groupdf = df.groupby(['City']).sum()
    groupdf['City'] = groupdf.index
    melted_df = pd.melt(groupdf, id_vars=['City'], value_vars=['Negative_Feedback', 'Positive_Feedback'])
    sns.set(rc={"xtick.labelsize": 14, "ytick.labelsize": 14, "axes.labelsize": 16, "axes.titlesize": 18})
    plt.figure(figsize=(15, 20))
    ax = sns.barplot(x='value', y='City', hue='variable', data=melted_df, orient='h')
    for p in ax.patches:
        ax.annotate(f'{p.get_width():.2f}', (p.get_width(), p.get_y() + p.get_height() / 2),
                    ha='center', va='center', fontsize=10, color='black', xytext=(5, 0),
                    textcoords='offset points', weight='bold')
    plt.xlabel('Feedback Count')
    plt.ylabel('City', fontsize=14, fontweight='bold')
    plt.title('Negative and Positive Feedback by City')
    plt.tight_layout()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer




def create_pdf_with_header(buffer,top5,worst5,feedbacks,pie1,pie2,pie3):
    pdf = FPDF()
    
    pdf.add_page()
    available_width = pdf.w - 2 * pdf.l_margin
    image_size = 10  # Adjust the size as needed
    pdf.set_font("Arial", "B", 16)
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, txt="January Month Rajasthan Police Report", ln=True, align='C')

    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)
    pdf.set_line_width(1.05)
    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(20)  # Move down a bit
    pdf.set_font("Arial", "B", 20)
    pdf.cell(available_width, 10, txt="Overview", ln=True, align='L')

    pdf.ln(5)  # Move down a bit
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, txt=f"Number of Feedbacks this Month: {feedbacks}", ln=True, align='L')
    
    pie1 = Image.open(pie1)
    pie2 = Image.open(pie2)
    pie3 = Image.open(pie3)

    pdf.ln(5)  # Move down a bit
    pdf.image(pie1, x=pdf.l_margin, y=pdf.get_y(), w=available_width/2)
    pdf.image(pie2, x=pdf.l_margin + available_width/2, y=pdf.get_y(), w=available_width/2)
    pdf.ln(90)
    pdf.image(pie2, x=pdf.l_margin, y=pdf.get_y(), w=available_width/2)
    pdf.image(pie3, x=pdf.l_margin + available_width/2, y=pdf.get_y(), w=available_width/2)

    pdf.add_page()
    image_size = 10  # Adjust the size as needed

    pdf.set_font("Arial", "B", 16)

    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)

    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, txt="January Month Rajasthan Police Report", ln=True, align='C')


    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)


    pdf.set_line_width(1.05)


    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    pdf.ln(20)  # Move down a bit
    pdf.set_font("Arial", "B", 20)
    pdf.cell(available_width, 10, txt="Top 5 Performing Police Stations", ln=True, align='L')


    img = Image.open(top5)
    img_width, img_height = img.size


    image_aspect_ratio = img_width / img_height
    new_width = available_width
    new_height = new_width / image_aspect_ratio

    pdf.image(top5, x=pdf.l_margin, y=pdf.get_y(), w=new_width, h=new_height)


    pdf.ln(new_height+5)  # Move down a bit
    pdf.set_font("Arial", "B", 20)
    pdf.cell(available_width, 10, txt="Worst 5 Performing Police Stations", ln=True, align='L')


    img = Image.open(worst5)
    img_width, img_height = img.size


    image_aspect_ratio = img_width / img_height
    new_width = available_width
    new_height = new_width / image_aspect_ratio

    pdf.image(worst5, x=pdf.l_margin, y=pdf.get_y(), w=new_width, h=new_height)    
    
    pdf.add_page()
    image_size = 10  # Adjust the size as needed

    pdf.set_font("Arial", "B", 16)

    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)

    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, txt="January Month Rajasthan Police Report", ln=True, align='C')


    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)


    pdf.set_line_width(1.05)


    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    pdf.ln(10)  # Move down a bit
    pdf.set_font("Arial", "B", 20)
    pdf.cell(available_width, 10, txt="City Wise Feedbacks", ln=True, align='L')
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




def plot_grouped_bar_chart_as_pdf(data):
    fig, ax = plt.subplots(figsize=(10, 6))

    data.plot(kind='bar', x='policeStation', stacked=True, ax=ax)

    ax.set_xlabel('Police Station')
    ax.set_ylabel('Count')
    ax.set_title('Negative and Positive Feelings by Police Station')
    ax.legend(title='Feelings', loc='upper right')
    pdf_bytes = BytesIO()
    with PdfPages(pdf_bytes) as pdf:
        pdf.savefig(fig, bbox_inches='tight')
    plt.close()

    return pdf_bytes.getvalue()

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