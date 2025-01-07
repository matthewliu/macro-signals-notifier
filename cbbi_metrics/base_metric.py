from abc import ABC, abstractmethod
import traceback
from typing import Any, Optional

import pandas as pd
from matplotlib.axes import Axes

from api.cbbiinfo_api import cbbi_fetch
from utils import send_error_notification

class BaseMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def _calculate(self, df: pd.DataFrame, ax: Optional[list[Axes]]) -> pd.Series:
        pass

    def _fallback(self, df: pd.DataFrame) -> pd.Series:
        df = df.merge(cbbi_fetch(self.name), on='Date', how='left')
        df['Value'] = df['Value'].ffill()
        return df['Value']

    async def calculate(self, df: pd.DataFrame, ax: Optional[list[Axes]]) -> pd.Series:
        try:
            return self._calculate(df, ax)
        except Exception as ex:
            traceback.print_exc()
            await send_error_notification(ex)
            print(f' Requesting fallback values for {self.name} (from CBBI.info) ')
            return self._fallback(df)
