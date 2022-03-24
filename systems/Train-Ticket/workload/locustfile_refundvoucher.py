from locust import LoadTestShape
from locustfile_pptam import  UserRefundVoucher
from util import tick, create_next_usercount

UserRefundVoucher.weight = 1

class Shape(LoadTestShape):
    next_usercount = create_next_usercount(UserRefundVoucher)

    def tick(self):
        return tick(self.__class__.next_usercount,
                    self.get_current_user_count(),
                    self.get_run_time())