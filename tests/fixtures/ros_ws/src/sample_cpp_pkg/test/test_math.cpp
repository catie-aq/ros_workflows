#include <gtest/gtest.h>

#include <stdexcept>

#include "sample_cpp_pkg/math.hpp"

TEST(MathTest, ClampInside)
{
  EXPECT_EQ(sample_cpp_pkg::clamp(5, 0, 10), 5);
}

TEST(MathTest, ClampOutside)
{
  EXPECT_EQ(sample_cpp_pkg::clamp(-3, 0, 10), 0);
  EXPECT_EQ(sample_cpp_pkg::clamp(42, 0, 10), 10);
}

TEST(MathTest, SumTo)
{
  EXPECT_EQ(sample_cpp_pkg::sum_to(100), 5050);
}
