.. currentmodule:: bitstring

.. _quick_reference:

###############
Quick Reference
###############

This section gives a summary of the bitstring module's classes, functions and attributes.

There are four classes that are bit containers, so that each element is a single bit.
They differ based on whether they can be modified after creation and on whether they have the concept of a current bit position.

.. list-table::
   :widths: 30 15 15 40
   :header-rows: 1

   * - Class
     - Mutable?
     - Streaming methods?
     -
   * - ``Bits``
     - ✘
     - ✘
     - An efficient, immutable container of bits.
   * - ``BitArray``
     - ✔
     - ✘
     - Like ``Bits`` but it can be changed after creation.
   * - ``ConstBitStream``
     - ✘
     - ✔
     - Immutable like ``Bits`` but with a bit position and reading methods.
   * - ``BitStream``
     - ✔
     - ✔
     - Mutable like ``BitArray`` but with a bit position and reading methods.


The final class is a flexible container whose elements are fixed-length bitstrings.

.. list-table::
   :widths: 30 15 15 40

   * - ``Array``
     - ✔
     - ✘
     - An efficient list-like container where each item has a fixed-length binary format.

----

Contents
""""""""

.. toctree::
   :maxdepth: 1

   quick_ref
