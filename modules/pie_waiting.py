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

def generate_pie_waiting(df):
    sum_column1 = df['Waiting_None'].sum()
    sum_column2 = df['Waiting_Five'].sum()
    sum_column3 = df['Waiting_Ten'].sum()
    sum_column4 = df['Waiting_Fifteen'].sum()
    sum_column5 = df['Waiting_More_Fifteen'].sum()

    sum_values = [sum_column1, sum_column2, sum_column3, sum_column4, sum_column5]

    labels = ['Immediately', '5 Mins', '10 Mins', '15 Mins', 'More Than 15 Mins']

    plt.figure(figsize=(6, 6))
    sns.set_palette("pastel")
    plt.pie(x=sum_values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Waiting Period Distribution')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()

    return img_buffer