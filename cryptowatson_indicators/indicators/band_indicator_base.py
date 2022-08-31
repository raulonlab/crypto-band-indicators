from typing import Union


class BandDetails:
    band_index=0
    band_ordinal=''
    name=''
    color=''
    multiplier=1
        

class BandIndicatorBase:
    _band_thresholds=[]
    _band_names=[]
    _band_colors=[]

    def get_band_at(self) -> Union[int, None]:
        pass

    def get_band_details_at(self) -> Union[BandDetails, None]:
        pass

    def plot_axes(self):
        pass

