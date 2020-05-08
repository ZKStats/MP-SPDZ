/*
 * ReplicatedPrep.h
 *
 */

#ifndef PROTOCOLS_REPLICATEDPREP_H_
#define PROTOCOLS_REPLICATEDPREP_H_

#include "Networking/Player.h"
#include "Processor/Data_Files.h"
#include "Processor/OnlineOptions.h"
#include "Processor/Machine.h"
#include "Protocols/Rep3Share.h"
#include "Protocols/ShuffleSacrifice.h"
#include "Math/gfp.h"
#include "edabit.h"

#include <array>

template<class T>
void buffer_inverses(vector<array<T, 2>>& inverses, Preprocessing<T>& prep,
        MAC_Check_Base<T>& MC, Player& P);

template<class T>
class BufferPrep : public Preprocessing<T>
{
    template<class U, class V> friend class Machine;

protected:
    vector<array<T, 3>> triples;
    vector<array<T, 2>> squares;
    vector<array<T, 2>> inverses;
    vector<T> bits;
    vector<vector<InputTuple<T>>> inputs;

    vector<dabit<T>> dabits;
    map<pair<bool, int>, vector<edabitvec<T>>> edabits;
    map<pair<bool, int>, edabitvec<T>> my_edabits;

    int n_bit_rounds;

    SubProcessor<T>* proc;

    virtual void buffer_triples() = 0;
    virtual void buffer_squares() { throw runtime_error("no squares"); }
    virtual void buffer_inverses() { throw runtime_error("no inverses"); }
    virtual void buffer_bits() { throw runtime_error("no bits"); }
    virtual void buffer_inputs(int player);

    // don't call this if T::Input requires input tuples
    void buffer_inputs_as_usual(int player, SubProcessor<T>* proc);

    virtual void buffer_dabits(ThreadQueues* = 0) { throw runtime_error("no daBits"); }
    virtual void buffer_edabits(int, ThreadQueues*) { throw runtime_error("no edaBits"); }
    virtual void buffer_sedabits(int, ThreadQueues*) { throw runtime_error("no sedaBits"); }

    virtual void buffer_edabits(bool strict, int n_bits,
            ThreadQueues* queues = 0);
    virtual void buffer_edabits_with_queues(bool strict, int n_bits);

    map<int, vector<dabit<T>>> personal_dabits;
    void get_personal_dabit(int player, T& a, typename T::bit_type& b);
    virtual void buffer_personal_dabits(int)
    { throw runtime_error("no personal daBits"); }

public:
    typedef T share_type;

    int buffer_size;

    static void basic_setup(Player& P) { (void) P; }
    static void setup(Player& P, typename T::mac_key_type alphai) { (void) P, (void) alphai; }
    static void teardown() {}

    BufferPrep(DataPositions& usage);
    virtual ~BufferPrep();

    void clear();

    void get_three_no_count(Dtype dtype, T& a, T& b, T& c);
    void get_two_no_count(Dtype dtype, T& a, T& b);
    void get_one_no_count(Dtype dtype, T& a);
    void get_input_no_count(T& a, typename T::open_type& x, int i);
    void get_no_count(vector<T>& S, DataTag tag, const vector<int>& regs,
            int vector_size);

    T get_random_from_inputs(int nplayers);

    virtual void get_dabit(T& a, typename T::bit_type& b);
    virtual void get_dabit_no_count(T& a, typename T::bit_type& b);
    virtual void get_edabits(bool strict, size_t size, T* a,
            vector<typename T::bit_type>& Sb, const vector<int>& regs);
    virtual void get_edabit_no_count(bool strict, int n_bits, edabit<T>& a);

    void push_triples(const vector<array<T, 3>>& triples)
    { this->triples.insert(this->triples.end(), triples.begin(), triples.end()); }
    void push_triple(const array<T, 3>& triple)
    { this->triples.push_back(triple); }

    void shrink_to_fit();

    void buffer_personal_triples(int, ThreadQueues*) {}
    void buffer_personal_triples(vector<array<T, 3>>&, int, int) {}

    SubProcessor<T>* get_proc() { return proc; }
    void set_proc(SubProcessor<T>* proc) { this->proc = proc; }
};

template<class T>
class BitPrep : public virtual BufferPrep<T>
{
protected:
    int base_player;

    typename T::Protocol* protocol;

    void buffer_ring_bits_without_check(vector<T>& bits, PRNG& G,
            int buffer_size);

public:
    BitPrep(SubProcessor<T>* proc, DataPositions& usage);

    void set_protocol(typename T::Protocol& protocol);

    void buffer_squares();

    void buffer_bits_without_check();
};

template<class T>
class RingPrep : public virtual BitPrep<T>
{
    typedef typename T::bit_type::part_type BT;

protected:
    size_t sent;

    void buffer_dabits_without_check(vector<dabit<T>>& dabits,
            int buffer_size = -1, ThreadQueues* queues = 0);
    void buffer_edabits_without_check(int n_bits, vector<T>& sums,
            vector<vector<typename T::bit_type::part_type>>& bits, int buffer_size,
            ThreadQueues* queues = 0);
    void buffer_edabits_without_check(int n_bits, vector<edabitvec<T>>& edabits,
            int buffer_size);

    void buffer_personal_edabits(int n_bits, vector<T>& sums,
            vector<vector<BT>>& bits, SubProcessor<BT>& proc, int input_player,
            bool strict, ThreadQueues* queues = 0);

    virtual void buffer_sedabits_from_edabits(int);

public:
    RingPrep(SubProcessor<T>* proc, DataPositions& usage);
    virtual ~RingPrep() {}

    vector<T>& get_bits() { return this->bits; }

    void sanitize(vector<edabit<T>>& edabits, int n_bits,
            int player = -1, ThreadQueues* queues = 0);
    void sanitize(vector<edabit<T>>& edabits, int n_bits, int player, int begin,
            int end);

    void buffer_dabits_without_check(vector<dabit<T>>& dabits,
            size_t begin, size_t end);
    void buffer_dabits_without_check(vector<dabit<T>>& dabits,
            size_t begin, size_t end,
            Preprocessing<typename T::bit_type::part_type>& bit_prep);

    void buffer_edabits_without_check(int n_bits, vector<T>& sums,
            vector<vector<typename T::bit_type::part_type>>& bits, int begin,
            int end);

    void buffer_personal_edabits_without_check(int n_bits, vector<T>& sums,
            vector<vector<BT> >& bits, SubProcessor<BT>& proc, int input_player,
            int begin, int end);

    virtual size_t data_sent() { return sent; }
};

template<class T>
class SemiHonestRingPrep : public virtual RingPrep<T>
{
public:
    SemiHonestRingPrep(SubProcessor<T>* proc, DataPositions& usage) :
            BufferPrep<T>(usage), BitPrep<T>(proc, usage),
			RingPrep<T>(proc, usage)
    {
    }
    virtual ~SemiHonestRingPrep() {}

    virtual void buffer_bits() { this->buffer_bits_without_check(); }
    virtual void buffer_inputs(int player)
    { this->buffer_inputs_as_usual(player, this->proc); }

    virtual void buffer_dabits(ThreadQueues*)
    { this->buffer_dabits_without_check(this->dabits); }
    virtual void buffer_edabits(int n_bits, ThreadQueues*)
    { this->buffer_edabits_without_check(n_bits, this->edabits[{false, n_bits}],
            OnlineOptions::singleton.batch_size); }
    virtual void buffer_sedabits(int n_bits, ThreadQueues*)
    { this->buffer_sedabits_from_edabits(n_bits); }
};

template<class T>
class MaliciousRingPrep : public virtual RingPrep<T>
{
protected:
    void buffer_edabits_from_personal(bool strict, int n_bits,
            ThreadQueues* queues);
    void buffer_personal_dabits(int input_player);

public:
    MaliciousRingPrep(SubProcessor<T>* proc, DataPositions& usage) :
            BufferPrep<T>(usage), BitPrep<T>(proc, usage),
            RingPrep<T>(proc, usage)
    {
    }
    virtual ~MaliciousRingPrep() {}

    virtual void buffer_bits();
    virtual void buffer_dabits(ThreadQueues* queues);
    virtual void buffer_edabits(bool strict, int n_bits, ThreadQueues* queues);
};

template<class T>
class ReplicatedRingPrep : public virtual BitPrep<T>
{
protected:
    void buffer_triples();
    void buffer_squares();

public:
    ReplicatedRingPrep(SubProcessor<T>* proc, DataPositions& usage) :
            BufferPrep<T>(usage), BitPrep<T>(proc, usage)
    {
    }

    virtual ~ReplicatedRingPrep() {}

    virtual void buffer_bits() { this->buffer_bits_without_check(); }
};

template<class T>
class ReplicatedPrep : public virtual ReplicatedRingPrep<T>,
        public virtual SemiHonestRingPrep<T>
{
    void buffer_inverses();

public:
    ReplicatedPrep(SubProcessor<T>* proc, DataPositions& usage) :
            BufferPrep<T>(usage), BitPrep<T>(proc, usage),
            ReplicatedRingPrep<T>(proc, usage),
            RingPrep<T>(proc, usage),
            SemiHonestRingPrep<T>(proc, usage)
    {
    }

    ReplicatedPrep(DataPositions& usage, int = 0) :
            ReplicatedPrep(0, usage)
    {
    }

    void buffer_squares() { ReplicatedRingPrep<T>::buffer_squares(); }
    void buffer_bits();
};

#endif /* PROTOCOLS_REPLICATEDPREP_H_ */
