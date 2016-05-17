VOLTTRON Historian Framework Introduction
-----------------------------------------

Historian Agents are the way by which device, actuator, datalogger, and
analysis are captured and stored in some sort of data store. Historian
Agents for `sMAP <sMAP-Historian>`__, general support for `SQL based
database <SQL-Historian>`__ (sqlite and MySql), and an
`OpenEIS <Analyitics-Historian>`__ stores already exist.

-  :doc:`SQL Historian<SQL-Historian>`
-  :doc:`Mongodb Historian<Mongo-Historian>`
-  :doc:`OpenEIS Historian <Analytics-Historian>`
-  :doc:`sMAP Historian <sMAP-Historian>`

Other implementations of historians can be created by following the
:doc:`developing historian agents <../..devguides/agent_development/Developing-Historian-Agents>` section of
the wiki.

Historians are all built upon the BaseHistorian which provides general
functionality the specific implementations build upon.

| By default the base historian will listen to 4 separate root topics
(datalogger/*, record/*, actuators/\ *, and device/*. Each of root
topics has a :doc:`specific message syntax <Historian-Topic-Syntax>` that
it is expecting
| for incoming data. Messages that are published to actuator are assumed
to be part of the actuation process. Messages published to datalogger
will be assumed to be timepoint data that is composed of units and
specific types with the assumption that they have the ability to be
graphed easily. Messages published to devices are data that comes
directly from drivers. Finally Messages that are published to record
will be handled as string data and can be customized to the user
specific situation. Please consult the :doc:`Historian Topic
Syntax <Historian-Topic-Syntax>` page for a specific syntax.

| This base historian will cache all received messages to a local
database
| before publishing it to the historian. This allows recovery for
unexpected
| happenings before the successful writing of data to the historian.
