==============================
Cenit Integrations Odoo Client
==============================

Cenit Integrations Odoo Client allows you to integrate your Odoo system with
many third party services available over the internet using the `server.cenit.io`_
platform as data integrator.

Overview
========

+ The `server.cenit.io`_ platform provides a set of models that allow you to map your
  data once and send it transparently to any service supported by the platform.
+ The `server.cenit.io`_ platform is free and community friendly, and makes use of
  open source and standards so that community driven development is easier.

Requirements
============

The Cenit Integrations Odoo Client requires a few additional Python packages to
be installed on your system. These dependencies can be easily installed using
**pip** as follows:

    $ pip install inflect

    $ pip install requests[security]

If not using **pip** you should manually install the following Python packages:

+ `inflect`
+ `pyOpenSSL`
+ `ndg-httpsclient`
+ `pyasn1`

Actual package names depend on your specific system.

Documentation
=============

The Cenit Integrations Odoo Client groups its provided models in two categories
describing *what* data you want to be able to send/receive and *when* you want
to send/receive the data.

Data definitions
################

The models gathered here describe the *what*, they manipulate the Odoo data to
shape it in a way that is consistent with supported third party services.

Libraries
+++++++++

*Libraries* are a mere logical organization of the data. They exist solely for
the purpose of organizing *Schemas* and *Data types*.

Fields
------

+ ``name``: string

  The name of the *Library*.

  Must be unique.

+ ``slug``: string

  A sanitized string containing only lower case alphanumeric characters and
  underscores.

  It identifies the *Library* and must therefore be unique.

Schemas
+++++++

*Schemas* are the fundamental stone of the `Server.cenit.io`_ platform models. They
define the way data is stored and transmitted.

Fields
------

+ ``library``: reference

  The *Library* to which the *Schema* belongs.

+ ``name``: string

  The name of the *Schema*.

  Must be unique for each *Library*.

+ ``slug``: string

  A sanitized string containing only lowercase alphanumeric characters and
  underscores.

  Must be unique for each *Library*.

+ ``schema``: string

  The actual JSON schema describing the data.

Data types
++++++++++

*Data types* represent a mapping between an existing Odoo model and a *Schema*.

Fields
------

+ ``name``: string

  The name of the *Data type*.

+ ``model``: reference

  The Odoo model that will by associated with the *Data type*.

+ ``library``: reference

  The *Library* to which the *Data type* belongs.

+ ``schema``: reference

  The *Schema* against which the ``model`` will be mapped.

+ ``enabled``: boolean

  If unchecked the *Data type* will be stored but won't trigger any event.
  This is most useful when the mapping is intended to be used embedded from
  another *Data type*.

+ ``mapping``: structure

  Describes how to translate the ``model`` to the ``schema``.
  It consists of a series of **mapping lines**, describing which ``model``
  data should go into which ``schema`` property.

  - ``name``: string

    the name of the ``schema`` property that will store the value expressed in
    ``value``.

  - ``value``: string

    represents an actual value to use, depending on the ``type``.

  - ``type``: one of

    - ``Field``: tells the *Data type* that the value expressed in ``value`` is
      the name of a field in the ``model`` (say **name**). This does not
      allow using nested fields (that is: **rel_id.name** will cause breakdown).

    - ``Model``: tells the *Data type* that the value expressed in ``value`` is
      a reference to other *Data type*. This means that when sending/receiving
      the data, the related Odoo model will also be serialized/deserialized
      (according to the specified ``reference``) and fully processed as if it
      were the one that triggered the action.

    - ``Reference``: tells the *Data type* that the value expressed in
      ``value`` is a reference to other model not mapped by any *Data type*. In
      this case the field **name** of the related model is used as an
      identifier.

    - ``Default``: tells the *Data type* that the value expressed in ``value``
      should be treated as a string literal, which can contain replacement
      patterns in the form of **{field_name}** where **field_name** is the
      name of a field in the ``model``.

      This form does allow the use of nested fields (e.g: **{rel_id.name}**),
      and also can be a json structure, in which case the JSON brackets should
      be doubled: **{{** and **}}** (e.g: **{{client: "{client.name}"}}**).

    - ``Python code``: tells the *Data type* that the value expressed in
      ``value`` should be evaluated (it is actually processed by a call to
      Python's **eval** builtin function). The special variable **obj** refers
      to the object being mapped.

  - ``reference``: reference

    used when ``type`` is **Model**.

    This refers to a *Data type* against which the ``value`` is mapped.

  - ``cardinality``: one of

    - ``2one``: the ``value`` represents a single object.

    - ``2many``: the ``value`` represents a list of objects.

    used when ``type`` is **Model** or **Reference**.

  - ``primary``: if checked, the field will be used as an identifier when
    receiving data.

+ ``triggers``: one of
  - ``On creation``: every time an instance of ``model`` is created on Odoo, a
    serialization to ``schema`` will be performed.

  - ``On update``: every time an existing instance of ``model`` is modified in
    Odoo, a serialization to ``schema`` will be performed.

  - ``On creation or update``: every time instance of ``model`` is created or
    modified, a serialization to ``schema`` will be performed.

  - ``On interval``: every 10 minutes all instances of ``model`` will be
    serialized to ``schema``.

  - ``Only manually``: serialization will only be performed when specifically
    requested to Odoo.

+ ``Conditions``: structure

  - ``field``: string

    The name of a field in ``model``.

  - ``condition``: one of

    - ``Equal``: the value of ``field`` for the instance of ``model`` being
      serialized must be equal to ``value``.

    - ``Different``: the value of ``field`` for the instance of ``model`` being
      serialized must be different than ``value``.

    - ``In``: the value of ``field`` for the instance of ``model`` being
      serialized must be present in ``value``.

    - ``Not in``: the value of ``field`` for the instance of ``model`` being
      serialized must not be present in ``value``.

  - ``value``: string

    If ``condition`` is one of ``In`` or ``Not in``, ``value`` will be splitted
    by **commas** to form a list.

Contribute
==========

+ Fork `the repository`_ on Github.
+ Create a branch off **8.0**
+ Make your changes
+ Write a test which shows that the bug was fixed or that the feature works as
  expected.
+ Send a pull request.

License
=======

    Copyright (C) 2014-2015 by Cenit IO Team <support [at] cenit [dot] io>

    All rights reserved.

    Cenit Integrations Odoo Client is licensed under the LGPL license.  You can
    redistribute and/or modify the Cenit Integrations Odoo Client according to
    the terms of the license.

.. _Cenit IO: https://server.cenit.io
.. _the repository: https://github.com/cenit-io/odoo-cenit
