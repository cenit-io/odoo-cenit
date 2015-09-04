=========================
Cenit Integrations Client
=========================

Cenit Integrations Client allows you to integrate your Odoo system with many
third party services available over the internet using the `cenitsaas`_
platform as data integrator.

Overview
========

- The `cenitsaas`_ platform provides a set of models that allow you to map your
  data once and send it transparently to any service supported by the platform.

- The `cenitsaas`_ platform is free and community friendly, and makes use of
  open source and standards so that community driven development is easier.

Requirements
============

The Cenit Integrations Client requires a few additional Python packages to be
installed on your system. These dependencies can be easily installed using
**pip** as follows:

$ pip install inflect

$ pip install requests[security]

If not using **pip** you should manually install the following Python packages:

- inflect
- pyOpenSSL
- ndg-httpsclient
- pyasn1

Actual package names depend on your specific system.

Documentation
=============

The Cenit Integrations Client groups its provided models in two categories
describing *what* data you want to be able to send/receive and *when* you want
to send/receive the data.

Data definitions
++++++++++++++++

The models gathered here describe the *what*, they manipulate the Odoo data to
shape it in a way that is consistent with supported third party services.

**Libraries**
+++++++++++++

*Libraries* are a mere logical organization of the data. They exist solely for
the purpose of organizing *Schemas* and *Data types*.

Fields
++++++

  - ``name``: string
    The name of the *Library*.

**Schemas**
+++++++++++

*Schemas* are the fundamental stone of the `cenitsaas`_ platform models. They
define the way data is stored and transmitted.

Fields
++++++

  - ``library``: reference

    The *Library* to which the *Schema* belongs.

  - ``uri``: string

    Identifies the *Schema* and must therefore be unique for each *Library*.

    It is commonly formed by the name of the *Schema* followed by an extension
    describing the format used (currently supported are 'json' and 'xml').

  - ``schema``: string

    The actual schema describing the data. It should match the extension
    provided in the **uri**.

    It can be blank (thought that wouldn't do much).

**Data types**
++++++++++++++

*Data types* represent a mapping between an existing Odoo model and a *Schema*.

Fields
++++++

  - ``name``: string

    The name of the *Data type*.

  - ``model``: reference

    The Odoo model that will by associated with the *Data type*.

  - ``library``: reference

    The *Library* to which the *Data type* belongs.

  - ``schema``: reference

    The *Schema* against which the **model** will be mapped.

  - ``active``: boolean

    If unchecked the *Data type* will be stored but not used.

  - ``mapping``: structure

    The **mapping** describes how to translate the **model** to the **schema**.
    It consists of a series of **mapping** lines, describing which **model**
    data should go into which **schema** property.

    - ``odoo``: represents an actual value to use.

    - ``cenit``: the name of the property that will store the value expressed in
      **odoo**.

    - ``type``: one of

      - ``field``: tells the *Data type* that the value expressed in **odoo** is
        the name of a field in the **model** (say ``name``). This does not
        allow using nested fields (that is: ``rel_id.name`` will cause
        breakdown).

      - ``model``: tells the *Data type* that the value expressed in **odoo** is
        a reference to other *Data type*. This means that when sending/receiving
        the data, the related Odoo model will also be serialized/deserialized
        (according to the specified *Data type*) and fully processed as if it
        were the one that triggered the action.

      - ``reference``: tells the *Data type* that the value expressed in
        **odoo** is a reference to other model not mapped by any *Data type*. In
        this case the field ``name`` of the related model is used as an
        identifier.

      - ``default``: tells the *Data type* that the value expressed in **odoo**
        should be treated as a string literal, which can contain replacement
        patterns in the form of ``{field_name}`` where ``field_name`` is the
        name of a field in the **model**.

        This form does allow the use of nested fields (e.g: ``{rel_id.name}``).
        Also the value of a default field can be a json structure, in which case
        the json brackets should be doubled: ``{{`` and ``}}`` (e.g:
        ``{{client: "{client.name}"}}``).

    - ``reference``: used when **type** is ``Model``.

      This refers to a *Data type* against which the value of **odoo** is
      mapped.

    - ``cardinality``: used when **type** is ``Model``.

      This refers to whether the value of **odoo** represents a single object
      (``2one``) or many (``2many``).

    - ``primary``: if checked, the field will be used as an identifier when
      receiving data.

Contribute
==========

#. Fork `the repository`_ on Github.
#. Create a branch off **8.0**
#. Make your changes
#. Write a test which shows that the bug was fixed or that the feature
   works as expected.
#. Send a pull request.

License
=======

::

    Copyright (C) 2014-2015 by CenitSaas Team <support at cenitsaas.com>

    All rights reserved.

    Cenit Integrations Client is licensed under the LGPL license.  You can
    redistribute and/or modify the Cenit Integrations Client according to the
    terms of the license.

.. _cenitsaas: https://cenitsaas.com
.. _the repository: https://github.com/openjaf/odoo-cenit