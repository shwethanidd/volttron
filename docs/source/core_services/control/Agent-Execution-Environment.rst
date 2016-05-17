Used Environmental Variables
============================

The following table lists the environmental variables that can be set during
the execution of an agent and/or VOLTTRON instance.  The VOLTTRON instance
will pass on the environmental variables automatically during the agent
process creation process.

.. csv-table:: Environmental Variables
   :header: "Context", "Variable", "Description"
   :widths: 20, 20, 50

   Agent/Platform, VOLTTRON_VIP_ADDR, "The router address an agent is/will attempt to connect to."
   Agent, AGENT_CONFIG, "The path to a configuration file to use during agent launch."
   Agent/Platform, VOLTTRON_HOME, "The home directory where the volttron instances is located."
