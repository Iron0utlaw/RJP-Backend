from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

def generate_pie_guidance(df):
    sum_column1 = df['Guidance_Poor'].sum()
    sum_column2 = df['Guidance_Below_Average'].sum()
    sum_column3 = df['Guidance_Average'].sum()
    sum_column4 = df['Guidance_Good'].sum()
    sum_column5 = df['Guidance_Excellent'].sum()

    sum_values = [sum_column1, sum_column2, sum_column3, sum_column4, sum_column5]

    labels = ['Poor', 'Below Average', 'Average', 'Good', 'Excellent']

    plt.figure(figsize=(6, 6))
    sns.set_palette("pastel")
    plt.pie(x=sum_values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Guidance Distribution')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()

    return img_buffer