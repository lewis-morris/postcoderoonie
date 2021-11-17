import datetime
import os
import csv
import shutil

from flask import current_app

from postcoderoonie.models import Places
from postcoderoonie import create_app, db

app = create_app()
def get_bool(txt):
    return txt.lower() in ["true", "yes"]

with app.app_context() as app:


    with open("/home/lewis/Desktop/postcodes.csv", newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        p = -1
        for row in spamreader:
            p += 1
            if p != 0:
                for i,ro in enumerate(row):
                    if ro == "":
                        row[i] = None
                    else:
                        try:
                            row[i] = float(row[i])
                        except:
                            pass
                        try:
                            row[i] = datetime.datetime.strptime(row[i], "%Y-%m-%d")
                        except:
                            pass

                place = Places(postcode=row[0],active=get_bool(row[1]),
                       lat=row[2],long=row[3],easting=row[4],northing=row[5],plus_code=row[45],altitude=row[26],
                       county=row[7], district=row[8], ward=row[9], country=row[12], parish=row[17],region=row[25], itl_one=row[49], itl_two=row[50], type=row[24],
                       date_introduced=row[15], date_terminated=row[16], last_updated=row[38],
                       population=row[19], households=row[20], average_income=row[46],
                       nearest_train=row[39], distance_to_train=row[40], police=row[43],sewage_company=row[47],water_company=row[44]
                )
                db.session.add(place)
            
            if p != 0 and p % 100 == 0:
                db.session.commit()



