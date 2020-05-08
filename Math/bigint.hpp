/*
 * bigint.hpp
 *
 */

#ifndef MATH_BIGINT_HPP_
#define MATH_BIGINT_HPP_

#include "bigint.h"
#include "Integer.h"

template<class T>
mpf_class bigint::get_float(T v, Integer exp, T z, T s)
{
    bigint tmp = v;
    mpf_class res = tmp;
    if (exp > 0)
        mpf_mul_2exp(res.get_mpf_t(), res.get_mpf_t(), exp.get());
    else
        mpf_div_2exp(res.get_mpf_t(), res.get_mpf_t(), -exp.get());
    if (z.is_one())
        res = 0;
    if (s.is_one())
    {
        res *= -1;
    }
    if (not z.is_bit() or not s.is_bit())
      {
        cerr << "z=" << z << " s=" << s << endl;
        throw Processor_Error("invalid floating point number");
      }
    return res;
}

template<class U, class T>
void bigint::output_float(U& o, const mpf_class& x, T nan)
{
    assert(nan.is_bit());
    if (nan.is_zero())
        o << x;
    else
        o << "NaN";
}

#endif /* MATH_BIGINT_HPP_ */
