
Install python project:
-----------------------
    virtualenv venv
    pip install -r requirements.txt
    ./manage.py companies_house


The scraper downloads `persons-with-significant-control-snapshot.zip` as one file
from http://download.companieshouse.gov.uk/en_pscdata.html into the project `downloads` folder.

After that it will process the file into `outputs` folder.
