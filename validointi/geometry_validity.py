# -*- coding: utf-8 -*-
"""
Created on Fri Aug 12 14:07:51 2022

@author: smassine
"""
from shapely.validation import explain_validity

def checkGeometryValidity(data, geom_column):
    
    """
    A Function for checking geometry validity.

    Parameters
    ----------
    data: <geopandas.GeoDataFrame>

        A GeoDataFrame containing Shapely geometries in a geometry column.
        
    geom_column: <str>
    
        Name of the geometry column in GeoDataFrame.
    
    Output
    ------
    <geopandas.GeoDataFrame>
    
        A GeoDataFrame containing a column named 'validity' with validity explanations.
 
    """
    
    #data['validity'] = data.apply(lambda row: explain_validity(row[geom_column]), axis=1)
    
    data['validity'] = None

    for index, row in data.iterrows():
        
        try:
            validity = explain_validity(row[geom_column])
            data[index:index+1]['validity'] = validity
        
        except OSError:
            print("Exception")
            print(row[geom_column])
            data[index:index+1]['validity'] = 'Valid Geometry'
    
    return(data)

def calculateGeometryValidityPercentage(data):
    
    """
    A Function for calculating a geometry validity percent for GeoDataFrane geometries.

    Parameter
    ----------
    data: <geopandas.GeoDataFrame>

        A GeoDataFrame containing validity information (run checkGeometryValidity-function first!).
        
    Output
    ------
    <str print>
    
        A percentage of valid geometries in a GeoDataFrame.
 
    """
    
    validity_list = dict(data.validity.value_counts())
    invalid_geometries = 0
    valid_geometries = 0
    
    for item in validity_list.items():
        if item[0] == 'Valid Geometry':
            valid_geometries = valid_geometries + item[1]
        else:
            invalid_geometries = invalid_geometries + item[1]
            
    validity_percent = (valid_geometries / (valid_geometries + invalid_geometries))*100
    answer = str(round(validity_percent, 2))
    
    return(print(answer + " %"))