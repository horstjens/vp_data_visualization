import pandas as pd

print("""
expecting those files:
clean_raw_data.csv:
    (x and y stands for numbers)
    ANGL_x          (angle of generator with NODE number)
    POWR_x          (power (p) of generator with NODE number)
    VARS_x          (q value of generator with NODE number)    
    PLOD_x          (p value of loads with NODE number)
    QLOD_x          (q value of loads with NODE number)
    POWR_x_TO_y     (p value of cable between nodes x,y) 
    VARS_x_TO_y     (q value of cable between nodes x,y)
clean_cables_mva.csv: 
    from_bus
    to_bus
    mva
clean_geodata.csv:
    Node
    Latitude
    Longitude
    Generator       (generator number or nothing)
    mva_generator   (mva of this generator or nothing)
    Load            (Yes or nothing)
    
# VARS: Reactive power (Q) of generator (can be used in conjunction with POWR above in the calculation of % of rating, ie % of MVA value = sqrt(P^2+Q^2) x 100 x 100 / MVA rating)    
""")

df_cables = pd.read_csv("clean_cables_mva.csv")
df_geo    = pd.read_csv("clean_geodata.csv")
df_raw    = pd.read_csv("clean_raw_data.csv")
df_new = pd.DataFrame() # empty

raw_col_names = list(df_raw.columns)

print("---- getting node values ----")
#col_names = [col_name for col_name in df_raw if col_name.startswith("VOLT_")]
col_names = []
node_generator = {} # key: node_number value:generator_number
generator_mva = {}
cable_mva = {}
#print("col_names", col_names)
node_numbers = df_geo["Node"]
#print(list(node_numbers))
for line, node_number in enumerate(node_numbers):
    #print("processing node #", node_number)
    this_col_name = f"VOLT_{node_number}"
    if this_col_name in df_raw:
        col_names.append(this_col_name)
        #print("found and added ", this_col_name)
    gen_number = df_geo.iloc[line]["Generator"]
    if not pd.isna(gen_number):
        #print("found generator: ", gen_number)
        node_generator[node_number] = int(gen_number)
        generator_mva[gen_number] = df_geo.iloc[line]["mva_generator"]
        raw_name1 = f"ANGL_{node_number}"
        my_name1 = f"ANGL_{gen_number}"
        raw_name2 = f"POWR_{node_number}"
        my_name2 = f"POWR_{gen_number}"
        raw_name3 = f"VARS_{node_number}"
        my_name3 = f"VARS_{gen_number}"
        if all((raw_name1 in raw_col_names, raw_name2 in raw_col_names, raw_name3 in raw_col_names)):
            col_names.append(raw_name1)
        else:
            print(f"PROBLEM: could not find all those column names in raw_data: {raw_name1},{raw_name2},{raw_name3}. Column skipped. ")
        #col_names.append(raw_name2)
        #col_names.append(raw_name3)
        #print(raw_name1 , "-->", my_name1)
    loads_yes = df_geo.iloc[line]["Load"]
    if not pd.isna(loads_yes):
        #print("found loads", loads_yes)
        if f"PLOD_{node_number}" in raw_col_names:
            col_names.append(f"PLOD_{node_number}")
        else:
            print(f'PROBLEM: could not find column {f"PLOD_{node_number}"} in raw data. Skipping this Load')
        #col_names.append(f"QLOD_{node_number}")
print("processing cables:")
cable_from = df_cables["from_bus"]
cable_to   = df_cables["to_bus"]
for line, node_number in enumerate(cable_from):
    nn_from = cable_from.iloc[line]
    nn_to   = cable_to.iloc[line]
    mva     = df_cables.iloc[line]["mva"]
    raw_name4 = f"POWR_{nn_from}_TO_{nn_to}"
    raw_name5 = f"VARS_{nn_from}_TO_{nn_to}"
    raw_name6 = f"POWR_{nn_to}_TO_{nn_from}"
    raw_name7 = f"VARS_{nn_to}_TO_{nn_from}"
    if all((raw_name4 in raw_col_names, raw_name5 in raw_col_names, raw_name6 in raw_col_names, raw_name7 in raw_col_names)):
        col_names.append(raw_name4)
    else:
        print(f'PROBLEM: Could not find all those column names in raw data: {raw_name4}, {raw_name5}, {raw_name6}, {raw_name7}. cable skipped')
    #col_names.append(raw_name5)
    if (nn_from, nn_to) not in cable_mva:
        cable_mva[(nn_from, nn_to)] = mva
    if (nn_to, nn_from) not in cable_mva:
        cable_mva[(nn_to, nn_from)] = mva


print("good col names:", col_names)
print("node2generator:", node_generator)
print("cable_mva:", cable_mva)

# create new columns in df_new
# start with the volts

#for col_name in col_names:
#    if col_name.startswith("VOLT_"):
#        # create new column
#        df_new.loc[:, col_name] = df_raw[col_name]
#        ##df_new.loc[:, col_name] = df_raw.drop(col_name, axis=1, inplace=True)
#        # delete column in old df to save memory
#        df_raw.drop(col_name, axis=1, inplace=True)
#df_raw.drop([name for name in col_names if name.startswith("VOLT_")],axis=1, inplace=True )
print("time column")
df_new.loc[:,"Time(s)"] = df_raw["Time(s)"]
# generators
print("processing columns....")
for col_name in col_names:
    if col_name.startswith("VOLT_"):
        print("node:", col_name)
        # create new column
        df_new.loc[:, col_name] = df_raw[col_name]
        # delete column in old df to save memory
        df_raw.drop(col_name, axis=1, inplace=True)
    elif col_name.startswith("ANGL_"):
        node_number = int(col_name[5:])
        gen_number = node_generator[node_number]
        print("generator",node_number, gen_number)
        df_new.loc[:, f"generator_angle_{gen_number}"] = df_raw[col_name]
        df_new.loc[:, f"generator_power_{gen_number}"] = df_raw[f"POWR_{node_number}"] * 100  # CHANGE
        # calculate %loading value
        loadings = []
        for line, value in enumerate(df_raw[col_name]):
            # % of MVA value = sqrt(P^2+Q^2) x 100 x 100 / MVA rating
            #   Data.df[new_name] = Data.df.apply(lambda row: row[colname]/mva * 100 * 100, axis=1)
            percent_of_mva_value = (df_raw.iloc[line][f"POWR_{node_number}"]**2 + df_raw.iloc[line][f"VARS_{node_number}"]**2)**0.5 * 100 * 100 / generator_mva[gen_number]
            #percent_of_mva_value = ((df_raw.iloc[line][f"POWR_{node_number}"]) ** 2 + df_raw.iloc[line][
            #    f"VARS_{node_number}"] ** 2) ** 0.5 * 100 * 100 / generator_mva[gen_number]

            loadings.append(percent_of_mva_value)
        df_new.loc[:,f"generator_loading_{gen_number}"] = loadings
        df_raw.drop(f"ANGL_{node_number}", axis=1, inplace=True)
        df_raw.drop(f"POWR_{node_number}", axis=1, inplace=True)
        df_raw.drop(f"VARS_{node_number}", axis=1, inplace=True)
        # delete old columns
    elif col_name.startswith("PLOD_"):
        load_number = int(col_name[5:])
        print("loads", load_number)
        df_new.loc[:,f"load_power_{load_number}"] = df_raw[col_name] * 1 # CHANGE
        df_raw.drop(f"PLOD_{load_number}", axis=1, inplace=True)
        df_raw.drop(f"QLOD_{load_number}", axis=1, inplace=True)
    elif all((col_name.startswith("POWR_"), "_TO_" in col_name)):
        print("cable", col_name)
        pos1 = col_name.find("_TO_")
        from_node_number = int(col_name[5:pos1])
        to_node_number = int(col_name[pos1+4:])

        powers = []
        loadings = []
        flows = []
        losses = []
        for line, value in enumerate(df_raw[col_name]):
            # find out flow sign
            power_a_to_b = df_raw.iloc[line][col_name]
            power_b_to_a = df_raw.iloc[line][f"POWR_{to_node_number}_TO_{from_node_number}"]
            loss = abs(power_a_to_b + power_b_to_a)  # one is always negative, the other always positive
            if power_a_to_b >= power_b_to_a:
                flow = 1
                power = power_a_to_b
                q = df_raw.iloc[line][f"VARS_{from_node_number}_TO_{to_node_number}"]
            else:
                flow = -1
                power = power_b_to_a
                q = df_raw.iloc[line][f"VARS_{to_node_number}_TO_{from_node_number}"]
            # Data.df[new_name] = Data.df.apply(lambda row: max(row[colname1],row[colname2]) / mva * 100, axis=1)
            percent_of_mva_value = (power**2 + q**2) ** 0.5 * 100  / cable_mva[(from_node_number, to_node_number)]
            powers.append(power)
            loadings.append(percent_of_mva_value)
            flows.append(flow)
            losses.append(loss)
        df_new.loc[:, f"cable_power_{from_node_number}_{to_node_number}"] = powers
        df_new.loc[:, f"cable_flow_{from_node_number}_{to_node_number}"] = flows
        df_new.loc[:, f"cable_loss_{from_node_number}_{to_node_number}"] = losses
        df_new.loc[:, f"cable_loading_{from_node_number}_{to_node_number}"] = loadings
        df_raw.drop(f"POWR_{from_node_number}_TO_{to_node_number}", axis=1, inplace=True)
        df_raw.drop(f"VARS_{from_node_number}_TO_{to_node_number}", axis=1, inplace=True)
        df_raw.drop(f"POWR_{to_node_number}_TO_{from_node_number}", axis=1, inplace=True)
        df_raw.drop(f"VARS_{to_node_number}_TO_{from_node_number}", axis=1, inplace=True)


print("writing csv...")
df_new.to_csv("simulation_data.csv")
print("writing of 'simulation_data.csv' is finished.")


