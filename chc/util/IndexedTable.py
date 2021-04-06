# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------

from typing import Callable, Dict, List, Generic, Optional, Tuple, TypeVar
import xml.etree.ElementTree as ET


class IndexedTableError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


def get_rep(node: ET.Element) -> Tuple[int, List[str], List[int]]:
    tags = node.get("t")
    args = node.get("a")
    try:
        if tags is None:
            taglist = []
        else:
            taglist = tags.split(",")
        if args is None or args == "":
            arglist = []
        else:
            arglist = [int(x) for x in args.split(",")]
        index_str = node.get("ix")
        if index_str is None:
            raise Exception("node " + str(node) + " did not have an ix element")
        index = int(index_str)
        return (index, taglist, arglist)
    except Exception as e:
        print("tags: " + str(tags))
        print("args: " + str(args))
        print(e)
        raise


def get_key(tags: List[str], args: List[str]) -> Tuple[str, str]:
    return (",".join(tags), ",".join([str(x) for x in args]))


class IndexedTableValue(object):
    def __init__(self, index: int) -> None:
        self.index = index

    def get_key(self) -> Tuple[str, str]:
        raise NotImplementedError("get_key not overridden")


class IndexedTableSuperclass:
    def __init__(self, name: str) -> None:
        self.name = name

    def size(self) -> int:
        raise NotImplementedError("size not overridden")

    def reset(self) -> None:
        raise NotImplementedError("reset not overridden")


V = TypeVar("V", bound=IndexedTableValue)


class IndexedTable(Generic[V], IndexedTableSuperclass):
    """Table to provide unique indices to objects represented by a key string.

    The table can be checkpointed and reset to that checkpoint with
    - set_checkpoint
    - reset_to_checkpoint

    Note: the string encodings use the comma as a concatenation character, hence
          the comma character cannot be used in any string representation.
    """

    def __init__(self, name: str) -> None:
        IndexedTableSuperclass.__init__(self, name)
        self.keytable: Dict[Tuple[str, str], int] = {}  # key -> index
        self.indextable: Dict[int, V] = {}  # index -> object
        self.next = 1
        self.reserved: List[int] = []
        self.checkpoint: Optional[int] = None

    def reset(self) -> None:
        self.keytable = {}
        self.indextable = {}
        self.next = 1
        self.reserved = []
        self.checkpoint = None

    def set_checkpoint(self) -> int:
        if self.checkpoint is None:
            self.checkpoint = self.next
            return self.next
        raise IndexedTableError(
            "Checkpoint has already been set at " + str(self.checkpoint)
        )

    def iter(self, f: Callable[[int, V], None]) -> None:
        for (i, v) in self.items():
            f(i, v)

    def reset_to_checkpoint(self) -> int:
        """Remove all entries added since the checkpoint was set."""
        cp = self.checkpoint
        if cp is None:
            raise ValueError("Cannot reset non-existent checkpoint")
        for i in range(cp, self.next):
            if i in self.reserved:
                continue
            self.indextable.pop(i)
        for k in self.keytable.keys():
            if self.keytable[k] >= cp:
                self.keytable.pop(k)
        self.checkpoint = None
        self.reserved = []
        self.next = cp
        return cp

    def remove_checkpoint(self) -> None:
        self.checkpoint = None

    def add(self, key: Tuple[str, str], f: Callable[[int, Tuple[str, str]], V]) -> int:
        if key in self.keytable:
            return self.keytable[key]
        else:
            index = self.next
            obj = f(index, key)
            self.keytable[key] = index
            self.indextable[index] = obj
            self.next += 1
            return index

    def reserve(self) -> int:
        index = self.next
        self.reserved.append(index)
        self.next += 1
        return index

    def values(self) -> List[V]:
        result: List[V] = []
        for i in sorted(self.indextable):
            result.append(self.indextable[i])
        return result

    def items(self) -> List[Tuple[int, V]]:
        result: List[Tuple[int, V]] = []
        for i in sorted(self.indextable):
            result.append((i, self.indextable[i]))
        return result

    def commit_reserved(self, index: int, key: Tuple[str, str], obj: V) -> None:
        if index in self.reserved:
            self.keytable[key] = index
            self.indextable[index] = obj
            self.reserved.remove(index)
        else:
            raise IndexedTableError("Trying to commit nonexisting index: " + str(index))

    def size(self) -> int:
        return self.next - 1

    def retrieve(self, index: int) -> V:
        if index in self.indextable:
            return self.indextable[index]
        else:
            msg = (
                "Unable to retrieve item "
                + str(index)
                + " from table "
                + self.name
                + " (size: "
                + str(self.size())
                + ")"
            )
            raise IndexedTableError(
                msg + "\n" + self.name + ", size: " + str(self.size())
            )

    def retrieve_by_key(
        self, f: Callable[[Tuple[str, str]], bool]
    ) -> List[Tuple[Tuple[str, str], V]]:
        result: List[Tuple[Tuple[str, str], V]] = []
        for key in self.keytable:
            if f(key):
                result.append((key, self.indextable[self.keytable[key]]))
        return result

    def write_xml(
        self, node: ET.Element, f: Callable[[ET.Element, V], None], tag: str = "n"
    ) -> None:
        for key in sorted(self.indextable):
            snode = ET.Element(tag)
            f(snode, self.indextable[key])
            node.append(snode)

    def read_xml(
        self,
        node: Optional[ET.Element],
        tag: str,
        get_value: Callable[[ET.Element], V],
        get_key: Callable[[V], Tuple[str, str]] = lambda x: x.get_key(),
        get_index: Callable[[V], int] = lambda x: x.index,
    ) -> None:
        if node is None:
            print("Xml node not present in " + self.name)
            raise IndexedTableError(self.name)
        for snode in node.findall(tag):
            obj = get_value(snode)
            key = get_key(obj)
            index = get_index(obj)
            self.keytable[key] = index
            self.indextable[index] = obj
            if index >= self.next:
                self.next = index + 1

    def __str__(self) -> str:
        lines: List[str] = []
        lines.append("\n" + self.name)
        for ix in sorted(self.indextable):
            lines.append(str(ix).rjust(4) + "  " + str(self.indextable[ix]))
        if len(self.reserved) > 0:
            lines.append("Reserved: " + str(self.reserved))
        if self.checkpoint is not None:
            lines.append("Checkpoint: " + str(self.checkpoint))
        return "\n".join(lines)
