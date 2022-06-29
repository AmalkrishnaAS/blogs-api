#write a function to scrape trending repositories on github

import requests
from bs4 import BeautifulSoup
import pprint

def scrape_repos():
    url = 'https://github.com/trending'
    base='https://github.com'
    response = requests.get(url,headers={'User-Agent': 'Mozilla/5.0'}).content
    # print(response)
    soup = BeautifulSoup(response, 'html.parser')
    # print(soup)
    #extract title and link
    headings = soup.find_all('h1',class_='lh-condensed')
    descriptions=soup.find_all('p',class_='col-9 color-fg-muted my-1 pr-4')
    languages=soup.find_all('span',itemprop='programmingLanguage')
    results = []
    for heading,description,language in zip(headings,descriptions,languages):
        results.append({
            'title':heading.text.replace('\n',''),
            'link':base+heading.find('a').get('href'),
            'description':description.text.replace('\n',''),
            'language':language.text
            
        })
        # print(results[0])
    return results
        
        
    
   
        
    
    


if __name__=='__main__':
    scrape_repos()  