def read_psl_demo_header(cds):
    # ...  <cube int: port><cube str: domain><cube int: mode num><cube str: map name>

    # one of these first unknowns is the unix timestamp
    unkn0 = cds.getint()
    unkn1 = cds.getint()
    unkn2 = cds.getint()
    unkn3 = cds.getint()

    port = cds.getint()

    domain = cds.getstring()

    mode_num = cds.getbyte()
    
    map_name = cds.getstring()
