#ifndef SAMPLE_CPP_PKG__MATH_HPP_
#define SAMPLE_CPP_PKG__MATH_HPP_

namespace sample_cpp_pkg
{

// Return value limited to [low, high]; low must not be greater than high.
int clamp(int value, int low, int high);

// Sum of the first n integers, computed in a loop (exercised by the sanitizer job).
long sum_to(int n);

}  // namespace sample_cpp_pkg

#endif  // SAMPLE_CPP_PKG__MATH_HPP_
