
try to collect reuseable parts from a torext + mongodb based admin project

components include:

torext.admin.forms
------------------

- ``_Widget``

  this class is made for generating HTML elements that can be used in a form

- ``BaseForm``

  this class takes an ``torext.mongodb.Document`` instance to instantiate form object,
  which will do everything about form in a page


torext.admin.tables
-------------------

- ``BaseTable``

  this class also takes an ``torext.mongodb.Document`` instance to instantiate a table object,
  which will be responsible for documents showing (with pagination) and querying


torext.admin.core
-----------------

- ``AdminHandler``

  the bridge between raw requests and queried documents and form, table objects,
  provide simple and small granular api for constructing the admin system


there are some other components from torext that play an important role:


torext.params
-------------

- ``ParamSet``

  this class helps doing validation in both ``BaseTable`` and ``BaseForm``
