# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 09:47:07 2022

@author: smassine
"""

def compareKuntadataToKTJ(kunta_data, ktj_data, kuntanimi, kaavalajit, dissolve_kunta=False, **kwargs):
    
    """
    Mandatory parameters
    --------------------
    kunta_data: <gpd.GeoDataFrame>
        Input kaavadata from municipalities as a Geopandas Geodataframe.
    ktj_data: <gpd.GeoDataFrame>
        Input KTJ-data from MML as a Geopandas Geodataframe.
    kuntanimi: <str>
        Name of the wanted municipality.
    kaavalajit <list>, list item <str>
        A list including kaavalaji numbers to be examined. E.g. asemakaavat ['31', '33']
        Check all numbers from: https://koodistot.suomi.fi/codescheme;registryCode=rytj;schemeCode=RY_Kaavalaji

    Optional parameters
    -------------------
    dissolve_kunta <boolean>
        True/False (default False).
        True if there is a need to group kaavaindex rows to form a kaava.
        False if input data already has an individual kaava as a row.
    dissolve_column
        When dissolve_kunta=True
        Name of the column to be used when dissolving the data.
    
    Output
    ------
    <gpd.GeoDataFrame>
        Municipality's kaavadata with comparison information included.
    """
    
    import sys
    import geopandas as gpd
    from shapely.geometry import Polygon, LineString, Point, MultiPolygon , MultiLineString, MultiPoint

    import warnings
    warnings.filterwarnings("ignore")

    def get_DE9IM_pattern(geom1, geom2):
        pattern = geom1.relate(geom2)
        return(pattern)
    
    def topologically_equal_DE9IM(geom1, geom2):
        # Two geometries are topologically equal if their interiors intersect and no part of the interior or boundary of one geometry intersects the exterior of the other.
        # DE-9IM pattern: "T*F**FFF*"
        equals = geom1.relate_pattern(geom2, 'T*F**FFF*')
        return(equals)

    def calculate_iou(geom1, geom2):
        iou = round((geom1.intersection(geom2).area / geom1.union(geom2).area)*100, 2)
        return(iou)

    dissolve_column = kwargs.get('dissolve_column', None)

    kunta_pala = kunta_data.loc[kunta_data['kuntanimi'] == kuntanimi]
    kunta_pala = kunta_pala.loc[kunta_pala['kaavalaji'].isin(kaavalajit)]
    ktj_pala = ktj_data.loc[ktj_data['kuntanimi'] == kuntanimi]
    ktj_pala = ktj_pala.loc[ktj_pala['kaavalaji'].isin(kaavalajit)]
    
    # Check to see if datasets have the same CRS system
    if kunta_pala.crs['init'] != ktj_pala.crs['init']:
        # If not, comparison cannot be made. Sys exit.
        sys.exit("Your data must have the same coordinate reference system!")
    
    if dissolve_kunta == True:
        kunta_pala = kunta_pala.dissolve(by=dissolve_column)
        kunta_pala.reset_index(inplace=True)
    
    kunta_pala['area_ha'] = None
    kunta_pala['ktj_area_ha'] = None
    kunta_pala['de9im_pattern'] = None
    kunta_pala['topo_equal'] = None
    kunta_pala['iou'] = None
    kunta_pala['ktj_kaavatunnus'] = None
    kunta_pala['a_delta_%'] = None
    
    ktj_grouped = ktj_pala.groupby('kaavatunnus_1')
    
    for idx, row in kunta_pala.iterrows():
            
        geom1 = row['geometry']
        kunta_pala.at[idx, 'area_ha'] = geom1.area / 10000
        item_dict = {"knro":[], "iou":[], "pattern": [], "topo_equal": [], "ktj_area": [], "a_delta": []}
        print("---------")
        
        for key, value in ktj_grouped:
            
            kaava = value.dissolve(by='kaavatunnus_1')
            geom2 = kaava.at[kaava.index[0], 'geometry']
            
            if geom1.intersects(geom2) == True:
                
                iou = calculate_iou(geom1, geom2)
                print(iou)
                
                pattern = get_DE9IM_pattern(geom1, geom2)
                
                topo_equal = topologically_equal_DE9IM(geom1, geom2)
                if topo_equal == False:
                    if iou >= 98:
                        topo_equal = True
                        
                ktj_area = geom2.area / 10000
                
                try:
                    delta = round(((ktj_area - (geom1.area / 10000)) / (geom1.area / 10000)) * 100, 2)
                except TypeError:
                    delta = None
                
                item_dict['knro'].append(str(kaava.index[0]))
                item_dict['iou'].append(iou)
                item_dict['pattern'].append(pattern)
                item_dict['topo_equal'].append(topo_equal)
                item_dict['ktj_area'].append(ktj_area)
                item_dict['a_delta'].append(delta)
        
        if len(item_dict['iou']) >= 1:
            kunta_pala.at[idx, 'iou'] = max(item_dict['iou'])
            indeksimme = item_dict['iou'].index(max(item_dict['iou']))
            kunta_pala.at[idx, 'ktj_kaavatunnus'] = item_dict['knro'][indeksimme]
            kunta_pala.at[idx, 'topo_equal'] = item_dict['topo_equal'][indeksimme]
            kunta_pala.at[idx, 'de9im_pattern'] = item_dict['pattern'][indeksimme]
            kunta_pala.at[idx, 'ktj_area_ha'] = item_dict['ktj_area'][indeksimme]
            kunta_pala.at[idx, 'a_delta_%'] = item_dict['a_delta'][indeksimme]
        else:
            None
    
    #List missing KTj indices
    lista = kunta_pala['ktj_kaavatunnus'].tolist()
    puuttuvat = []
    
    for index, row in ktj_pala.iterrows():
        
        if row['kaavatunnus_1'] not in lista:
            puuttuvat.append(row['kaavatunnus_1'])    
    
    print("")
    print("Missing KTJ indices:")
    print(sorted(set(puuttuvat)))
    
    return(kunta_pala)
