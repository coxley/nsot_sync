nsot_sync
=========

The goal of ``nsot_sync`` is to translate from a driver (local computer
networks or another vendor's IPAM) to native NSoT resources.

It has been written to make adding extra drivers easy, based on a simple
contract.

TODO
----

Heavy development

* Finish docs
* Write tests

Driver Contract
---------------

Unfinished, reminder list for writing the real contract out

* Every resource must contain an 'attributes' key, even if empty dict

