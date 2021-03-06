import numpy as np
import sqlalchemy
import datetime as dt
from dateutil import parser
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

# date validation 
def isValidDate(date_string, format) :
    try:
        dt.datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False

# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)
Base.classes.keys()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Flask Setup
app = Flask(__name__)

# Flask Routes

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&#60;start&#62;<br/>"
        f"/api/v1.0/&#60;start&#62;/&#60;end&#62;"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():

    """Convert the query results to a dictionary using date as the key and prcp as the value."""

    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).limit(1).all()[0][0]
    most_recent_date = parser.parse(most_recent_date)
    one_year_ago = most_recent_date - dt.timedelta(days=365)
    results=session.query(Measurement.date, Measurement.prcp).filter(\
        Measurement.date >= one_year_ago.strftime('%Y-%m-%d'),\
        Measurement.date <= most_recent_date.strftime('%Y-%m-%d')).all()

    session.close()

    # Return the JSON representation of your dictionary.  
    all_precip = []
    for date, prcp in results:
        precip_dict = {}
        precip_dict["date"] = date
        precip_dict["prcp"] = prcp        
        all_precip.append(precip_dict)

    return jsonify(all_precip)


@app.route("/api/v1.0/stations")
def stations():

    """Return a JSON list of stations from the dataset."""   

    # Create our session (link) from Python to the DB
    session = Session(engine)

    results = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    # Return the JSON representation of your dictionary.  
    all_stations = []
    for id, station, name, latitude, longitude, elevation in results:
        station_dict = {}
        station_dict["id"] = id 
        station_dict["station"] = station
        station_dict["name"] = name  
        station_dict["latitude"] = latitude  
        station_dict["longitude"] = longitude  
        station_dict["elevation"] = elevation          
        all_stations.append(station_dict)        

    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():

    """Query the dates and temperature observations of the most active station for the last year of data"""   

    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    station = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).\
    order_by(func.count(Measurement.station).desc()).limit(1)[0][0]

    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).limit(1).all()[0][0]
    most_recent_date = parser.parse(most_recent_date)

    # Calculate the date one year from the last date in data set.
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Perform a query to retrieve the date and temperature data
    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station==station).\
        filter(Measurement.date >= one_year_ago.strftime('%Y-%m-%d'), Measurement.date <= most_recent_date.strftime('%Y-%m-%d')).\
        all()

    session.close()

    # Return the JSON representation of your dictionary.  
    all_tobs = []
    for date, tobs in results:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs        
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end=None):

    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a 
    given start or start-end range."""

    """"When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates 
    between the start and end date inclusive."""

    if end is None and not isValidDate(start, "%Y-%m-%d") :
         return jsonify({"error": f"Invalid date submitted. Must be in yyyy-mm-dd format."}), 404
    elif end is not None and ((not isValidDate(start, "%Y-%m-%d")) or (not isValidDate(end, "%Y-%m-%d"))) :
        return jsonify({"error": f"Invalid start/end date submitted. Both must be in yyyy-mm-dd format."}), 404

    # Create our session (link) from Python to the DB
    session = Session(engine)

    if end is None:
        results = session.query(func.min(Measurement.tobs).label("min"),\
        func.max(Measurement.tobs).label("max"),\
        func.avg(Measurement.tobs).label("avg"),
        func.count(Measurement.tobs).label("count")).\
        filter(Measurement.date >= start).\
        order_by(Measurement.date).all()
    else:
        results = session.query(func.min(Measurement.tobs).label("min"),\
        func.max(Measurement.tobs).label("max"),\
        func.avg(Measurement.tobs).label("avg"),\
        func.count(Measurement.tobs).label("count")).\
        filter(Measurement.date >= start, Measurement.date <= end).\
        order_by(Measurement.date).all()

    session.close()

     # Return the JSON representation of your dictionary.  
    all_tobs = []
    for min, max, avg, cnt in results:
        tobs_dict = {}
        tobs_dict["min"] = min 
        tobs_dict["max"] = max 
        tobs_dict["avg"] = avg 
        if end is None:
            tobs_dict[f"Recordset count for >= {start}"]  = cnt
        else:
            tobs_dict[f"Recordset count between {start} and {end}"]  = cnt              
        all_tobs.append(tobs_dict)

    return jsonify(all_tobs)


if __name__ == '__main__':
    app.run(debug=True)