import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO

# Function to generate a sample plot
def generate_plot():
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]

    plt.plot(x, y)
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.title('Sample Plot')
    plt.grid(True)

    # Save the plot to a file
    plt.savefig('sample_plot.png')
    plt.close()

# Function to create a PDF with a header, feedbacks line, and plot
def create_pdf_with_header():
    pdf = FPDF()
    pdf.add_page()

    # Calculate available width for the header
    available_width = pdf.w - 2 * pdf.l_margin

    # Set the images to be smaller and equal in size
    image_size = 10  # Adjust the size as needed

    # Add header with images on left, text in center, and image on right
    pdf.set_font("Arial", "B", 16)

    # Left image 1
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)

    # Left image 2
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, txt="January Month Rajasthan Police Report", ln=True, align='C')

    # Right image
    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)

    # Set line thickness
    pdf.set_line_width(1.05)

    # Draw a line across the page after the header
    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    # Add section heading "Overview"
    pdf.ln(20)  # Move down a bit
    pdf.set_font("Arial", "B", 20)
    pdf.cell(available_width, 10, txt="Overview", ln=True, align='L')

    # Add line displaying the number of feedbacks for the current month
    pdf.ln(5)  # Move down a bit
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, txt="Number of Feedbacks this Month: 50", ln=True, align='L')

    pdf.ln(5)  # Move down a bit
    pdf.image('gender_pie_chart.png', x=pdf.l_margin, y=pdf.get_y(), w=available_width/2)
    pdf.image('feedback_pie_chart.png', x=pdf.l_margin + available_width/2, y=pdf.get_y(), w=available_width/2)
    pdf.ln(80)
    pdf.image('feedback_pie_chart.png', x=pdf.l_margin, y=pdf.get_y(), w=available_width/2)
    pdf.image('gender_pie_chart.png', x=pdf.l_margin + available_width/2, y=pdf.get_y(), w=available_width/2)

    pdf.add_page()
    # Set the images to be smaller and equal in size
    image_size = 10  # Adjust the size as needed

    # Add header with images on left, text in center, and image on right
    pdf.set_font("Arial", "B", 16)

    # Left image 1
    pdf.image('left_image1.png', x=pdf.l_margin, y=pdf.t_margin, w=image_size)

    # Left image 2
    pdf.image('left_image2.png', x=pdf.l_margin + image_size + 5, y=pdf.t_margin, w=image_size+2)

    text_width = pdf.get_string_width("January Month Rajasthan Police Report")
    text_x = (available_width - text_width) / 2

    pdf.cell(text_x)  # Move to the calculated X position for centered text
    pdf.cell(text_width, 10, txt="January Month Rajasthan Police Report", ln=True, align='C')

    # Right image
    pdf.image('right_image.png', x=pdf.w - pdf.r_margin - image_size-5, y=pdf.t_margin-5, w=image_size+10)

    # Set line thickness
    pdf.set_line_width(1.05)

    # Draw a line across the page after the header
    pdf.ln(5)  # Move down a bit
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    pdf.ln(10)  # Move down a bit
    pdf.set_font("Arial", "B", 20)
    pdf.cell(available_width, 10, txt="Top 5 Performing Police Stations", ln=True, align='L')

    # Calculate the remaining page height
    remaining_height = pdf.h - pdf.get_y() - 15

    # Load the image for aspect ratio calculation
    img = plt.imread('sample_plot.png')

    # Calculate proportional height to maintain the aspect ratio
    image_aspect_ratio = img.shape[0] / img.shape[1]
    image_height = remaining_height / 2
    image_width = image_height / image_aspect_ratio

    pdf.image('sample_plot.png', x=pdf.l_margin + image_width/8, y=pdf.get_y(), w=image_width, h=image_height)

    # Add the heading for the worst performing police stations before the second image
    pdf.ln(image_height+5)  # Move down a bit
    pdf.set_font("Arial", "B", 20)
    pdf.cell(available_width, 10, txt="Worst 5 Performing Police Stations", ln=True, align='L')

    # Add the second image on the same page
    pdf.image('sample_plot.png', x=pdf.l_margin + image_width/8, y=pdf.get_y(), w=image_width, h=image_height)
    
    pdf.add_page()
    # data = [1, 2, 3, 4, 5]
    # plt.plot(data)
    # plt.xlabel('X-axis')
    # plt.ylabel('Y-axis')
    # plt.title('Your Plot Title')

    # Save the plot to a BytesIO object
    # buffer = BytesIO()
    # plt.savefig(buffer, format='png')
    # buffer.seek(0)

    # Load the image for aspect ratio calculation
    img = plt.imread('temp_image.png')

    # Calculate proportional height to maintain the aspect ratio
    image_aspect_ratio = img.shape[0] / img.shape[1]
    image_height = remaining_height / 2
    image_width = image_height / image_aspect_ratio

    # Reset the buffer position to the beginning
    # buffer.seek(0)

    # Use the plot directly in the PDF
    pdf.image('temp_image.png', x=pdf.l_margin + image_width/8, y=pdf.get_y(), w=available_width, h=pdf.h)

    # Save the PDF to a file
    pdf.output('output_with_header.pdf')


if __name__ == "__main__":
    generate_plot()
    create_pdf_with_header()
