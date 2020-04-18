from bs4 import BeautifulSoup
import json
import os
import pandas as pd
import re
import requests
import subprocess
# import pdftotext

def text_from_pdf(pdf_path):
    txt_path = pdf_path.replace("pdfs", "txts").replace(".pdf", ".txt")
    print("-----DEBUG----",txt_path)
    if not os.path.exists(os.path.dirname(txt_path)):
        os.makedirs(os.path.dirname(txt_path))
    if not os.path.exists(txt_path):
        # subprocess.call(["ls"])
        subprocess.call(["pdftotext", pdf_path, txt_path])
    f = open(txt_path, encoding="utf8")
    text = f.read()
    f.close()
    return text

# change the base_url to http://openaccess.thecvf.com/menu.py
base_url = "http://openaccess.thecvf.com/"

index_urls = {2020: "http://openaccess.thecvf.com/WACV2020.py",
2019:"http://openaccess.thecvf.com/CVPR2019.py",
2018:"http://openaccess.thecvf.com/CVPR2018.py",
2017:"http://openaccess.thecvf.com/CVPR2017.py",
2016:"http://openaccess.thecvf.com/CVPR2016.py",
2015:"http://openaccess.thecvf.com/CVPR2015.py",
2014:"http://openaccess.thecvf.com/CVPR2014.py",
2013:"http://openaccess.thecvf.com/CVPR2013.py"
}
print(index_urls.keys())


nips_authors = set()
papers = list()
paper_authors = list()

for year in sorted(index_urls.keys()):
    index_url = index_urls[year]
    index_html_path = os.path.join("working", "html", str(year)+".html")

    if not os.path.exists(index_html_path):
        r = requests.get(index_url)
        if not os.path.exists(os.path.dirname(index_html_path)):
            os.makedirs(os.path.dirname(index_html_path))
        with open(index_html_path, "wb") as index_html_file:
            index_html_file.write(r.content)
    with open(index_html_path, "rb") as f:
        print("--DEBUG--: open html file "+index_html_path)
        html_content = f.read()
        soup = BeautifulSoup(html_content, "lxml")

    links = soup.find_all('a')

    paper_links = []
    info_links = []
    conference_name = index_url[:-7]
    conference_name = conference_name[29:]
    print("conference_name",conference_name)

    for link in links:
        print (str(link)[9:32])
        if str(link)[9:32] == "content_"+conference_name+"_"+str(year)+"/html/":
            info_links.append(link)
        if str(link)[9:34] == "content_"+conference_name+"_"+str(year)+"/papers/":
            paper_links.append(link)

        if str(link)[9:32] == "content_"+conference_name.lower()+"_"+str(year)+"/html/":
            info_links.append(link)
        if str(link)[9:34] == "content_"+conference_name.lower()+"_"+str(year)+"/papers/":
            paper_links.append(link)

    # print("DEBUG:", len(paper_links) == len(info_links))
    print("%d Papers Found" % len(paper_links))
    # print("DEBUG:first link is ", paper_links[0])


    temp_path = os.path.join("working", "txt")

    count = 1
    for i in range(len(info_links)):
        infolink = info_links[i]
        paperlink = paper_links[i]
        print("paper_title:", infolink.contents[0])
        paper_title = infolink.contents[0]
        print("info link:", base_url+infolink["href"])
        info_link = base_url+infolink["href"]
        print("pdf_link: ", base_url+paperlink["href"])
        pdf_link = base_url+paperlink["href"]
        print("pdf_name:", paperlink["href"][25:] )
        pdf_name = paperlink["href"][25:]
        pdf_path = os.path.join("working", "pdfs", str(year), pdf_name)
        paper_id = year*10000 + count ##yyyy+xxxx(ID)
        count += 1
        print("pdf_path:", pdf_path)
        print("paper_id:", paper_id)

        ##write to the pdf file
        # if not os.path.exists(pdf_path):
        #     pdf = requests.get(pdf_link)
        #     if not os.path.exists(os.path.dirname(pdf_path)):
        #         os.makedirs(os.path.dirname(pdf_path))
        #     pdf_file = open(pdf_path, "wb")
        #     pdf_file.write(pdf.content)
        #     pdf_file.close()

        paper_info_html_path = os.path.join("working", "html", str(year), str(paper_id)+".html")
        if not os.path.exists(paper_info_html_path):
            r = requests.get(info_link)
            if not os.path.exists(os.path.dirname(paper_info_html_path)):
                os.makedirs(os.path.dirname(paper_info_html_path))
            with open(paper_info_html_path, "wb") as f:
                f.write(r.content)
        with open(paper_info_html_path, "rb") as f:
            html_content = f.read()
        paper_soup = BeautifulSoup(html_content, "lxml")
        try:
            abstract = paper_soup.find('div', attrs={"id": "abstract"}).contents[0]
            # print("----DEBUG----",abstract)
        except:
            print("Abstract not found %s" % paper_title.encode("ascii", "replace"))
            abstract = ""

        # authors = paper_soup.find('div', attrs={"id": "authors"})
        authors = str(paper_soup.find_all('i'))# e.g. <i>Lu Sang,  Bjoern Haefner,  Daniel Cremers</i>
        authors = authors[4:]
        authors = authors[:-5]
        all_authors = authors.split(',')
        # print("----DEBUG----",authors)

        authors.split(',')
        for author in all_authors:
            author = author.strip() #remove space
            if author != "":
                nips_authors.add(author)

        paper_authors.append([paper_id, all_authors])
        papers.append([paper_id, year, paper_title, abstract])

print("Writing to file.....")
pd.DataFrame(list(nips_authors), columns=["name"]).sort_values(by="name").to_csv("output/authors.csv", index=False)
pd.DataFrame(papers, columns=["id", "year", "title", "abstract"]).sort_values(by="id").to_csv("output/papers.csv", index=False)
pd.DataFrame(paper_authors, columns=["id", "author"]).sort_values(by="id").to_csv("output/paper_authors.csv", index=False)
print("Done!")
