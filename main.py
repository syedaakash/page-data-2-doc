import requests
import csv
import os
import qrcode
from bs4 import BeautifulSoup
from pyhtml2pdf import converter

data = []
data_dict = []

url = 'https://order.samoscafe.com'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    site_header = soup.find(class_='logoWrapper')
    footer_logo = site_header.find('img')['src'] if site_header.find('img') else None
    site_footer = soup.find(class_='templateFooter')
    footer_title = site_footer.find('h2').text
    footer_phone = site_footer.find(class_='locationPhone').text
    footer_address = site_footer.find(class_='locationAddress').text

    categories = soup.select('.menuSectionWrapper .menuWrapper')
    for category in categories:
        category_name = category.find('h2').text
        items = category.select('.itemSection .item')

        for item in items:
            title_el = item.find(class_='itemHeader')
            title = title_el.text.strip() if title_el else None

            description_el = item.select('.desktopDescription .itemDescription')
            description = description_el[0].text.strip() if description_el else None

            price_el = item.find(class_='price')
            price = price_el.text.strip() if price_el else None

            image_el = item.find('img')
            image_url = image_el['src'] if image_el else None

            availability = item.find('span', string='Out of stock')
            out_of_stock = availability.text.strip() if availability else None

            data.append([title.replace('*', ''), description, price, category_name, image_url, out_of_stock])
            data_dict.append({'title': title.replace('*', ''),
                              'description': description,
                              'price': price,
                              'category': category_name,
                              'image_url': image_url,
                              'out_of_stock': out_of_stock})

csv_file = "menu_items.csv"

with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Food Title', 'Food Description', 'Food Price', 'Food Category', 'Food Image', 'Stock Status'])
    writer.writerows(data)


def csv_to_html(csv_file, html_file):
    with open(csv_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = [row for row in reader]

    # Create HTML string
    html_content = '<html><head><title>CSV to HTML</title>'
    html_content += '<style>table {border-collapse: collapse; width: 100%;} th, td {border: 1px solid black; padding: 8px;} th {background-color: #f2f2f2;} tr:nth-child(even) {background-color: #f2f2f2;}</style>'
    html_content += '</head><body>'
    html_content += '<table>'
    for row in data:
        html_content += '<tr>'
        for cell in row:
            html_content += f'<td>{cell}</td>'
        html_content += '</tr>'
    html_content += '</table></body></html>'

    # Write HTML to file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


# html_file = 'menu_items.html'
# csv_to_html(csv_file, html_file)

grouped_data = {}
for item in data_dict:
    category = item['category']
    if category not in grouped_data:
        grouped_data[category] = []
    grouped_data[category].append(item)

footer_data = {
    'footer_logo': footer_logo,
    'footer_title': footer_title,
    'footer_phone': footer_phone,
    'footer_address': footer_address,
}


def generate_qr_code(data, filename):
    # Concatenate footer data into a single string
    footer_info = '\n'.join([f'{key}: {value}' for key, value in data.items()])

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(footer_info)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img.save(filename)


filename = "footer_qr_code.png"
generate_qr_code(footer_data, filename)


def generate_category_html(grouped_data, footer_data):
    html_content = '<html><head><title>Categories and Items</title>'
    html_content += '<style>.items-container {display: flex; flex-wrap: wrap;} .item-card {flex: 0 0 calc(50% - 22px); margin: 0 10px 10px 0; border: 1px solid #ccc; display: flex;} .item-card img {width: 100px;height: 100px; margin-right: 10px;} .item-details {flex-grow: 1;} .item-details h2 {font-size: 14px;} .item-details p {font-size: 12px;} @media print {.pagebreak {clear: both;page-break-after: always;}}</style>'
    html_content += '</head><body>'

    for category, items in grouped_data.items():
        html_content += '<h1>{}</h1>'.format(category)
        html_content += '<div class="items-container">'
        for idx, item in enumerate(items):
            if idx == 12:
                html_content += '<div class="pagebreak"> </div>'
            html_content += '<div class="item-card">'
            html_content += '<img src="{}" alt="{}">'.format(item['image_url'], item['title'])
            html_content += '<div class="item-details">'
            html_content += '<h2>{}</h2>'.format(item['title'])
            html_content += '<p>{}</p>'.format(item['description'])
            html_content += '<p><strong>Price:</strong> {}</p>'.format(item['price'])
            html_content += '<p>{}</p>'.format(item['out_of_stock'] if item['out_of_stock'] else '')
            html_content += '</div></div>'

        html_content += '</div>'
        # Footer section
        # html_content += '<div class="footer">'
        # html_content += '<div class="footer-info">'
        # html_content += '<p>{}</p>'.format(footer_data['footer_title'])
        # html_content += '<p>{}</p>'.format(footer_data['footer_phone'])
        # html_content += '<p>{}</p>'.format(footer_data['footer_address'])
        # html_content += '</div>'
        # Generate QR code for the right side
        # html_content += '<img src="{}" alt="QR Code" width="100" height="100">'.format(filename)
        html_content += '<div class="pagebreak"> </div>'

    html_content += '</div>'

    html_content += '</body></html>'

    return html_content


def generate_html_file(grouped_data, html_file):
    html_content = generate_category_html(grouped_data, footer_data)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


html_file2 = 'menu_items2.html'
generate_html_file(grouped_data, html_file2)

pdf_file = "menu_items.pdf"

path = os.path.abspath(html_file2)
converter.convert(f'file:///{path}', pdf_file)

print(f"Data extraction completed. {len(data)} items were written to {csv_file} and PDF was generated.")
