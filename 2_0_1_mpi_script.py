import numpy as np
from multiprocessing import Pool, cpu_count
import pickle
with open("2_0_0_analysisdata/2_0_0dfmpl_list.pkl","rb")as f:
    dfmpl_list = pickle.load(f)
def objective(params):
    threshold1, threshold2, v0_thres, v1_thres = params
    collated_data_list = []

    for dfmpl, _, _ in dfmpl_list:
        df_v = dfmpl.values
        changes = (df_v[:, 3] - df_v[:, 0]) / df_v[:, 0]
        a4_1 = np.logical_and(changes[1:] < threshold1, changes[:-1] < threshold2)
        locs = np.where(a4_1)[0]
        if locs.size > 0:
            chosen_locs = [loc for loc in locs if validate_df(loc, df_v, v0_thres, v1_thres)]
            if chosen_locs:
                collated_data = np.asarray([changes[loc:loc + 5] for loc in chosen_locs])
                collated_data_list.append(collated_data)

    collated_data = np.vstack(collated_data_list)
    mean_val = collated_data[:, 2].mean()
    return mean_val, params,collated_data[:, 2].size,list(collated_data[:, 2])

def validate_df(loc, df_v, v0_thres, v1_thres):
    v0 = df_v[loc, 0] * df_v[loc, 4]
    v1 = df_v[loc + 1, 0] * df_v[loc + 1, 4]
    return v0 > v0_thres and v1 > v1_thres
size=2
threshold1_values = np.linspace(-0.01, 0, size)
threshold2_values = np.linspace(-0.01, 0, size)
v0_thres_values = np.linspace(1e6, 5e6, size)
v1_thres_values = np.linspace(1e6, 5e6, size)

parameter_grid = [(threshold1, threshold2, v0_thres, v1_thres) 
                  for threshold1 in threshold1_values 
                  for threshold2 in threshold2_values 
                  for v0_thres in v0_thres_values 
                  for v1_thres in v1_thres_values]
if __name__ == "__main__":
    
    import time
    t0 = time.time()
    # Evaluate the objective function in parallel over the parameter grid
    with Pool(4)as pool:
        results = pool.map(objective, parameter_grid)
    t1=time.time()
    # Find the best parameters
    best_parameters = max(results, key=lambda x: x[0])[1]
    best_mean_val = max(results, key=lambda x: x[0])[0]
    with open("2_0_0_analysisdata/2_0_0mpi_run_results2.pkl","wb")as f:
        pickle.dump(results,f)
    print(f"time taken: {t1-t0:.2f}s")
    print('Best parameters:', best_parameters)
    print('Best mean value:', best_mean_val)