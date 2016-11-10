.. _DriverOverride:

Driver Override Specification
==============================
This document describes the specification for the override feature.
By default, every user is allowed write access to the devices by the master driver. The override feature will allow the user (for example, building administrator) to override this default behavior and enable the user to lock the write
access on the devices.

Functional Capabilities
-----------------------------

1. User shall be able to specify the following when turning on the override behavior.

    * Entity on which the override/lock feature has be applied. (example: campus/building/device/point1)

    * Whether override inheritance needs to be supported or not
      For example,

         If pattern is campus/building1/* - Override condition is turned on for all the devices under campus/building1

         If pattern is campus/building1/ahu1 - Override condition is turned on for only campus/building1/ahu1

    * Time duration over which override behavior is applicable

2. User shall also be able to disable/turn off the override behavior by specifying:
    * Entity on which the override/lock feature has be disabled. (example: campus/building/device/point1)

3. Master driver shall set all the set points falling under the override condition to its default state/value immediately. This is to ensure that the devices are in fail-safe state when the override/lock feature is removed/
turned off.

4. User shall be able to get a list of all the entities with override condition set.

Driver RPC Methods
********************
set_override_on( pattern, duration=0.0 ) - Turn on override condition on all the entities matching the pattern

set_override_off( pattern ) - Turn off override condition on all the entities matching the pattern

get_override_list( ) - Get a list of all the set points with override condition.
