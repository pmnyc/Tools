#ifndef OSMIUM_INDEX_RELATIONS_MAP_HPP
#define OSMIUM_INDEX_RELATIONS_MAP_HPP

/*

This file is part of Osmium (http://osmcode.org/libosmium).

Copyright 2013-2017 Jochen Topf <jochen@topf.org> and others (see README).

Boost Software License - Version 1.0 - August 17th, 2003

Permission is hereby granted, free of charge, to any person or organization
obtaining a copy of the software and accompanying documentation covered by
this license (the "Software") to use, reproduce, display, distribute,
execute, and transmit the Software, and to prepare derivative works of the
Software, and to permit third-parties to whom the Software is furnished to
do so, all subject to the following:

The copyright notices in the Software and this entire statement, including
the above license grant, this restriction and the following disclaimer,
must be included in all copies of the Software, in whole or in part, and
all derivative works of the Software, unless such copies or derivative
works are solely in the form of machine-executable object code generated by
a source language processor.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

*/

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <tuple>
#include <vector>

#include <osmium/osm/relation.hpp>
#include <osmium/osm/types.hpp>

namespace osmium {

    namespace index {

        namespace detail {

            template <typename TKey, typename TKeyInternal, typename TValue, typename TValueInternal>
            class flat_map {

            public:

                using key_type   = TKey;
                using value_type = TValue;

            private:

                struct kv_pair {
                    TKeyInternal key;
                    TValueInternal value;

                    explicit kv_pair(key_type key_id) :
                        key(static_cast<TKeyInternal>(key_id)),
                        value() {
                    }

                    kv_pair(key_type key_id, value_type value_id) :
                        key(static_cast<TKeyInternal>(key_id)),
                        value(static_cast<TValueInternal>(value_id)) {
                    }

                    bool operator<(const kv_pair& other) const noexcept {
                        return std::tie(key, value) < std::tie(other.key, other.value);
                    }

                    bool operator==(const kv_pair& other) const noexcept {
                        return std::tie(key, value) == std::tie(other.key, other.value);
                    }
                }; // struct kv_pair

                std::vector<kv_pair> m_map;

            public:

                using const_iterator = typename std::vector<kv_pair>::const_iterator;

                void set(key_type key, value_type value) {
                    m_map.emplace_back(key, value);
                }

                void sort_unique() {
                    std::sort(m_map.begin(), m_map.end());
                    const auto last = std::unique(m_map.begin(), m_map.end());
                    m_map.erase(last, m_map.end());
                }

                std::pair<const_iterator, const_iterator> get(key_type key) const noexcept {
                    return std::equal_range(m_map.begin(), m_map.end(), kv_pair{key}, [](const kv_pair& lhs, const kv_pair& rhs) {
                        return lhs.key < rhs.key;
                    });
                }

                bool empty() const noexcept {
                    return m_map.empty();
                }

                size_t size() const noexcept {
                    return m_map.size();
                }

            }; // class flat_map

        } // namespace detail

        /**
        * Index for looking up parent relation IDs given a member relation ID.
        * You can not instantiate such an index yourself, instead you need to
        * instantiate a RelationsMapStash, fill it and then create an index from
        * it:
        *
        * @code
        * RelationsMapStash stash;
        * ...
        * for_each_relation(const osmium::Relation& relation) {
        *    stash.add_members(relation);
        * }
        * ...
        * const auto index = stash.build_index();
        * ...
        * osmium::unsigned_object_id_type member_id = ...;
        * index.for_each_parent(member_id, [](osmium::unsigned_object_id_type id) {
        *   ...
        * });
        * ...
        * @endcode
        *
        */
        class RelationsMapIndex {

            friend class RelationsMapStash;

            using map_type = detail::flat_map<osmium::unsigned_object_id_type, uint32_t,
                                            osmium::unsigned_object_id_type, uint32_t>;

            map_type m_map;

            RelationsMapIndex(map_type&& map) :
                m_map(std::move(map)) {
            }

        public:

            RelationsMapIndex() = delete;

            RelationsMapIndex(const RelationsMapIndex&) = delete;
            RelationsMapIndex& operator=(const RelationsMapIndex&) = delete;

            RelationsMapIndex(RelationsMapIndex&&) = default;
            RelationsMapIndex& operator=(RelationsMapIndex&&) = default;

            /**
            * Find the given relation id in the index and call the given function
            * with all parent relation ids.
            *
            * @code
            * osmium::unsigned_object_id_type member_id = 17;
            * index.for_each_parent(member_id, [](osmium::unsigned_object_id_type id) {
            *   ...
            * });
            * @endcode
            *
            * Complexity: Logarithmic in the number of elements in the index.
            *             (Lookup uses binary search.)
            */
            template <typename Func>
            void for_each_parent(osmium::unsigned_object_id_type member_id, Func&& func) const {
                const auto parents = m_map.get(member_id);
                for (auto it = parents.first; it != parents.second; ++it) {
                    std::forward<Func>(func)(it->value);
                }
            }

            /**
            * Is this index empty?
            *
            * Complexity: Constant.
            */
            bool empty() const noexcept {
                return m_map.empty();
            }

            /**
            * How many entries are in this index?
            *
            * Complexity: Constant.
            */
            size_t size() const noexcept {
                return m_map.size();
            }

        }; // RelationsMapIndex

        /**
        * The RelationsMapStash is used to build up the data needed to create
        * an index of member relation ID to parent relation ID. See the
        * RelationsMapIndex class for more.
        */
        class RelationsMapStash {

            using map_type = detail::flat_map<osmium::unsigned_object_id_type, uint32_t,
                                            osmium::unsigned_object_id_type, uint32_t>;

            map_type m_map;

#ifndef NDEBUG
            bool m_valid = true;
#endif

        public:

            RelationsMapStash() = default;

            RelationsMapStash(const RelationsMapStash&) = delete;
            RelationsMapStash& operator=(const RelationsMapStash&) = delete;

            RelationsMapStash(RelationsMapStash&&) = default;
            RelationsMapStash& operator=(RelationsMapStash&&) = default;

            /**
            * Add mapping from member to parent relation in the stash.
            */
            void add(osmium::unsigned_object_id_type member_id, osmium::unsigned_object_id_type relation_id) {
                assert(m_valid && "You can't use the RelationsMap any more after calling build_index()");
                m_map.set(member_id, relation_id);
            }

            /**
            * Add mapping from all members to given parent relation in the stash.
            */
            void add_members(const osmium::Relation& relation) {
                assert(m_valid && "You can't use the RelationsMap any more after calling build_index()");
                for (const auto& member : relation.members()) {
                    if (member.type() == osmium::item_type::relation) {
                        m_map.set(member.positive_ref(), relation.positive_id());
                    }
                }
            }

            /**
            * Is this stash empty?
            *
            * Complexity: Constant.
            */
            bool empty() const noexcept {
                assert(m_valid && "You can't use the RelationsMap any more after calling build_index()");
                return m_map.empty();
            }

            /**
            * How many entries are in this stash?
            *
            * Complexity: Constant.
            */
            size_t size() const noexcept {
                assert(m_valid && "You can't use the RelationsMap any more after calling build_index()");
                return m_map.size();
            }

            /**
            * Build an index with the contents of this stash and return it.
            *
            * After you get the index you can not use the stash any more!
            */
            RelationsMapIndex build_index() {
                assert(m_valid && "You can't use the RelationsMap any more after calling build_index()");
                m_map.sort_unique();
#ifndef NDEBUG
                m_valid = false;
#endif
                return RelationsMapIndex{std::move(m_map)};
            }

        }; // class RelationsMapStash

    } // namespace index

} // namespace osmium

#endif // OSMIUM_INDEX_RELATIONS_MAP_HPP
