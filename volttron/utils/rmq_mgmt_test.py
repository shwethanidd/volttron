from volttron.utils.rmq_mgmt import *

def check_user_permissions():
    create_user("tempo", "temping")
    permissions = dict(configure="volttron1.tester|__pubsub__.volttron.*",
                       read="volttron1.tester|__pubsub__.volttron.*",
                       write= "volttron1.tester|__pubsub__.volttron.*")
    set_user_permissions(permissions, "tester", "testing")

check_user_permissions()