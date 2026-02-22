import numpy as np
from scipy.stats import norm

class SPCEngine:
    def __init__(self, usl=None, lsl=None, target=None):
        self.usl = usl
        self.lsl = lsl
        self.target = target

    def calculate_stats(self, data, subgroup_size=5):
        """
        Calculates stats and subgroup data for X-bar/R charts.
        """
        arr = np.array(data)
        mean = np.mean(arr)
        std_overall = np.std(arr, ddof=1)
        
        # Subgrouping logic for charts
        subgroups = [arr[i:i + subgroup_size] for i in range(0, len(arr), subgroup_size)]
        x_bar_data = [np.mean(sg) for sg in subgroups if len(sg) > 0]
        r_data = [np.max(sg) - np.min(sg) for sg in subgroups if len(sg) > 0]
        
        # Estimate within-subgroup variation (using R-bar/d2 for n=5, d2=2.326)
        if len(r_data) > 0:
            r_bar = np.mean(r_data)
            d2 = 2.326 if subgroup_size == 5 else 1.128 # fallback for n=2
            std_within = r_bar / d2
        else:
            std_within = std_overall 
            
        results = {
            "mean": mean,
            "std_overall": std_overall,
            "std_within": std_within,
            "min": np.min(arr),
            "max": np.max(arr),
            "count": len(arr),
            "subgroups": {
                "x_bar": x_bar_data,
                "r": r_data,
                "size": subgroup_size
            }
        }
        
        if self.usl is not None and self.lsl is not None:
            results.update(self._calculate_capability(mean, std_overall, std_within))
            
        return results

    def _calculate_capability(self, mean, std_overall, std_within):
        # Overall Capability (Pp/Ppk)
        pp = (self.usl - self.lsl) / (6 * std_overall)
        ppk = min((self.usl - mean) / (3 * std_overall), 
                  (mean - self.lsl) / (3 * std_overall))
        
        # Potential Capability (Cp/Cpk)
        cp = (self.usl - self.lsl) / (6 * std_within)
        cpk = min((self.usl - mean) / (3 * std_within), 
                  (mean - self.lsl) / (3 * std_within))
        
        return {
            "cp": cp,
            "cpk": cpk,
            "pp": pp,
            "ppk": ppk,
            "cpk_status": "PASS" if cpk >= 1.33 else "FAIL"
        }
